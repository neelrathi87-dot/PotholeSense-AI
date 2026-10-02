create table if not exists potholes (
  id uuid primary key default gen_random_uuid(),
  device_id text not null,
  lat double precision not null,
  lon double precision not null,
  confidence real not null,
  severity text not null check (severity in ('low','medium','high')),
  pothole_count int not null default 1,
  image_url text not null,
  status text not null default 'open' check (status in ('open','in_progress','fixed')),
  detected_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists potholes_geo_idx on potholes (lat, lon);
create index if not exists potholes_time_idx on potholes (detected_at desc);

alter table potholes enable row level security;

create policy "public read" on potholes for select using (true);
