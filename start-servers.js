const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const logFile = path.join(__dirname, 'servers.log');
const pidFile = path.join(__dirname, 'server.pid');

fs.writeFileSync(pidFile, process.pid.toString());

function writeLog(line) {
  const time = new Date().toISOString().replace('T', ' ').substring(0, 19);
  const formatted = `[${time}] ${line}\n`;
  try {
    fs.appendFileSync(logFile, formatted);
  } catch (e) {}
}

const banner = [
  '================================================================',
  ' 🚀 Starting PotholeSense Multi-Server Architecture (24/7 Mode)',
  '================================================================'
].join('\n');

console.log(banner);
writeLog(banner);

const procs = [];
let detectedTunnelUrl = null;
let isShuttingDown = false;

function handleLog(name, text, isErr) {
  const lines = text.toString().split('\n');
  lines.forEach(line => {
    const trimmed = line.trim();
    if (!trimmed) return;

    // Check for Cloudflare tunnel URL in both stdout and stderr
    if (trimmed.includes('trycloudflare.com')) {
      const match = trimmed.match(/https:\/\/[a-zA-Z0-9-]+\.trycloudflare\.com/);
      if (match && match[0] !== detectedTunnelUrl) {
        detectedTunnelUrl = match[0];
        fs.writeFileSync(path.join(__dirname, 'active_tunnel_url.txt'), detectedTunnelUrl);
        const urlBanner = [
          '',
          '================================================================',
          ' 🌐 CLOUDFLARE HTTPS TUNNEL IS ACTIVE AND RUNNING!',
          ` 📱 Mobile Patrol Link: ${detectedTunnelUrl}/mobile`,
          ` 💻 Web API Link      : ${detectedTunnelUrl}/health`,
          '================================================================',
          ''
        ].join('\n');
        console.log(urlBanner);
        writeLog(urlBanner);
      }
    }

    // Cloudflare logs normal info to stderr; don't label it as an error
    if (name === 'TUNNEL' && (trimmed.includes('INF') || trimmed.includes('precheck') || trimmed.includes('Registered tunnel'))) {
      writeLog(`[${name}] ${trimmed}`);
      return;
    }

    if (isErr) {
      if (trimmed.includes('DeprecationWarning') || trimmed.includes('DEP0190')) return;
      console.log(`[${name}] ${trimmed}`);
      writeLog(`[${name}] ${trimmed}`);
    } else {
      console.log(`[${name}] ${trimmed}`);
      writeLog(`[${name}] ${trimmed}`);
    }
  });
}

function startProcess(name, cmd, args, options = {}) {
  const p = spawn(cmd, args, {
    shell: true,
    stdio: ['ignore', 'pipe', 'pipe'],
    ...options
  });

  p.stdout.on('data', (data) => handleLog(name, data, false));
  p.stderr.on('data', (data) => handleLog(name, data, true));

  p.on('exit', (code) => {
    const exitMsg = `[${name}] Process stopped (code ${code})`;
    console.log(exitMsg);
    writeLog(exitMsg);
  });

  procs.push(p);
  return p;
}

// Keep event loop alive 24/7
setInterval(() => {}, 1000 * 60 * 60);

// 1. Start FastAPI AI Engine (Port 8000)
console.log('• Starting [1/3] FastAPI Detection Server (Port 8000)...');
writeLog('• Starting [1/3] FastAPI Detection Server (Port 8000)...');
startProcess('FASTAPI', 'python', ['-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000']);

// 2. Start Next.js Municipal Map Dashboard (Port 3000)
const dashboardDir = path.join(__dirname, 'dashboard');
console.log('• Starting [2/3] Next.js Dashboard (Port 3000)...');
writeLog('• Starting [2/3] Next.js Dashboard (Port 3000)...');
startProcess('NEXTJS', 'npm', ['run', 'dev'], { cwd: dashboardDir });

// 3. Start Cloudflare Tunnel (Port 8000 -> HTTPS) with Self-Healing Auto-Restart
function startTunnel() {
  const cloudflaredExe = path.join(__dirname, 'cloudflared.exe');
  if (fs.existsSync(cloudflaredExe)) {
    console.log('• Starting [3/3] Cloudflare Secure HTTPS Tunnel...');
    writeLog('• Starting [3/3] Cloudflare Secure HTTPS Tunnel...');
    const tunnelProc = startProcess('TUNNEL', cloudflaredExe, ['tunnel', '--url', 'http://127.0.0.1:8000']);
    tunnelProc.on('exit', (code) => {
      if (!isShuttingDown) {
        const restartMsg = `[TUNNEL] Cloudflare tunnel stopped (code ${code}). Auto-restarting in 5 seconds...`;
        console.log(restartMsg);
        writeLog(restartMsg);
        setTimeout(() => {
          if (!isShuttingDown) startTunnel();
        }, 5000);
      }
    });
  }
}
startTunnel();

const summary = [
  '----------------------------------------------------------------',
  ' 💻 Local Dashboard : http://localhost:3000',
  ' 📡 AI API Server   : http://localhost:8000',
  ' 📚 Swagger API Docs: http://localhost:8000/docs',
  ' Press Ctrl + C to stop all servers.',
  '----------------------------------------------------------------\n'
].join('\n');
console.log(summary);
writeLog(summary);

function cleanup() {
  isShuttingDown = true;
  console.log('\nStopping all servers...');
  writeLog('Stopping all servers...');
  try {
    if (fs.existsSync(pidFile)) fs.unlinkSync(pidFile);
  } catch (e) {}
  procs.forEach(p => {
    try { p.kill(); } catch (e) {}
  });
  process.exit();
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
