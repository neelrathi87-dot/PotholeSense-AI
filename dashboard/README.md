SERVER
1. Run server/schema.sql in the Supabase SQL editor
2. Create a public Storage bucket named potholes
3. cd server && cp .env.example .env and fill values
4. Copy best.pt into server/
5. pip install -r requirements.txt
6. uvicorn main:app --host 0.0.0.0 --port 8000

TEST
curl -X POST http://localhost:8000/detect -H "x-api-key: YOUR_KEY" -F "frame=@test.jpg" -F "lat=19.9975" -F "lon=73.7898"

PI
1. sudo apt install gpsd gpsd-clients
2. Plug in the USB GPS and run cgps -s to confirm a fix
3. pip install -r pi/requirements.txt
4. SERVER_URL=https://your-server API_KEY=YOUR_KEY python client.py

DASHBOARD
1. Run dashboard/realtime.sql in the Supabase SQL editor
2. cd dashboard && cp .env.local.example .env.local and fill values
3. npm install
4. npm run dev and open http://localhost:3000
5. Deploy: push to GitHub, import in Vercel, add the same env vars
