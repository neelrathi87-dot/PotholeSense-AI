import { createClient } from '@supabase/supabase-js';

const ALLOWED = ['open', 'in_progress', 'fixed'];

export async function POST(req) {
  const adminPass = process.env.ADMIN_PASSWORD || 'admin123';
  if (req.headers.get('x-admin-password') !== adminPass) {
    return Response.json({ error: 'Wrong admin password' }, { status: 401 });
  }

  const { id, status } = await req.json();
  if (!id || !ALLOWED.includes(status)) {
    return Response.json({ error: 'Invalid request' }, { status: 400 });
  }

  const sbUrl = process.env.SUPABASE_URL;
  const sbKey = process.env.SUPABASE_SERVICE_KEY;

  if (sbUrl && sbKey && !sbUrl.includes('YOUR-PROJECT')) {
    try {
      const sb = createClient(sbUrl, sbKey);
      const { error } = await sb.from('potholes').update({ status }).eq('id', id);
      if (error) {
        return Response.json({ error: error.message }, { status: 500 });
      }
      return Response.json({ ok: true });
    } catch (err) {
      return Response.json({ error: err.message }, { status: 500 });
    }
  }

  // Fallback to FastAPI server
  try {
    const res = await fetch(`http://localhost:8000/potholes/${id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': 'test-api-key-12345'
      },
      body: JSON.stringify({ status })
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      return Response.json({ error: body.detail || 'Backend update failed' }, { status: res.status });
    }
    return Response.json({ ok: true });
  } catch (err) {
    return Response.json({ error: 'Database update failed: ' + err.message }, { status: 500 });
  }
}
