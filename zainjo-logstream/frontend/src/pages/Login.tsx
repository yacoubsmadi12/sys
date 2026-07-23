import { useState, useEffect, useRef } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Lock, User, AlertCircle } from "lucide-react";
import zainLogo from "../assets/zain-logo.png";

/* ── Matrix rain canvas ─────────────────────────────────────────────────── */
function MatrixRain() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const chars = "アイウエオカキクケコサシスセソタチツテトナニヌネノ01ABCDEF@#$%&<>/\\[]{}ΣΩΔΨΦΛΞΠΘ";
    const fontSize = 13;
    const cols = () => Math.floor(canvas.width / fontSize);
    let drops: number[] = Array.from({ length: cols() }, () => Math.random() * -50);

    const draw = () => {
      ctx.fillStyle = "rgba(2, 6, 23, 0.18)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const numCols = cols();
      while (drops.length < numCols) drops.push(0);

      for (let i = 0; i < numCols; i++) {
        const ch = chars[Math.floor(Math.random() * chars.length)];
        const y = drops[i] * fontSize;

        // bright head
        ctx.fillStyle = "#00ffcc";
        ctx.font = `bold ${fontSize}px monospace`;
        ctx.fillText(ch, i * fontSize, y);

        // trailing glow
        ctx.fillStyle = "rgba(0,200,150,0.6)";
        ctx.font = `${fontSize - 1}px monospace`;
        const prevCh = chars[Math.floor(Math.random() * chars.length)];
        if (y > fontSize) ctx.fillText(prevCh, i * fontSize, y - fontSize);

        // reset
        if (y > canvas.height && Math.random() > 0.975) {
          drops[i] = 0;
        }
        drops[i]++;
      }
    };

    const id = setInterval(draw, 45);
    return () => {
      clearInterval(id);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full"
      style={{ opacity: 0.35 }}
    />
  );
}

/* ── Floating cyber nodes ────────────────────────────────────────────────── */
function CyberNodes() {
  const nodes = Array.from({ length: 18 }, (_, i) => ({
    id: i,
    top:  `${Math.random() * 90}%`,
    left: `${Math.random() * 90}%`,
    size: Math.random() * 4 + 2,
    delay: Math.random() * 4,
    dur:   Math.random() * 3 + 3,
  }));

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {nodes.map((n) => (
        <div
          key={n.id}
          className="absolute rounded-full bg-cyan-400"
          style={{
            top: n.top,
            left: n.left,
            width: n.size,
            height: n.size,
            boxShadow: `0 0 ${n.size * 4}px ${n.size * 2}px rgba(0,255,200,0.4)`,
            animation: `pulse ${n.dur}s ${n.delay}s ease-in-out infinite`,
          }}
        />
      ))}
    </div>
  );
}

/* ── Scan line ───────────────────────────────────────────────────────────── */
function ScanLine() {
  return (
    <div
      className="absolute inset-x-0 h-px pointer-events-none"
      style={{
        background: "linear-gradient(90deg, transparent, #00ffcc44, #00ffcc, #00ffcc44, transparent)",
        animation: "scandown 6s linear infinite",
        top: 0,
      }}
    />
  );
}

/* ── Main login page ─────────────────────────────────────────────────────── */
export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
    } catch {
      setError("Invalid username or password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 overflow-hidden"
         style={{ background: "#020617" }}>

      {/* ── Cyber keyframe styles ── */}
      <style>{`
        @keyframes scandown {
          0%   { top: 0; opacity: 0; }
          5%   { opacity: 1; }
          95%  { opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.3; transform: scale(1); }
          50%       { opacity: 1;   transform: scale(1.6); }
        }
        @keyframes gridpulse {
          0%, 100% { opacity: 0.07; }
          50%       { opacity: 0.14; }
        }
        @keyframes glowborder {
          0%, 100% { box-shadow: 0 0 0 1px rgba(0,255,200,0.15), 0 25px 60px rgba(0,0,0,0.7); }
          50%       { box-shadow: 0 0 0 1px rgba(0,255,200,0.35), 0 25px 60px rgba(0,0,0,0.7); }
        }
        @keyframes shimmer {
          0%   { left: -100%; }
          100% { left: 200%; }
        }
      `}</style>

      {/* Matrix rain */}
      <MatrixRain />

      {/* Animated grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(0,255,200,1) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,200,1) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
          animation: "gridpulse 4s ease-in-out infinite",
        }}
      />

      {/* Radial vignette to focus on center */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse 70% 70% at 50% 50%, transparent 30%, #020617 90%)",
        }}
      />

      {/* Scan line */}
      <ScanLine />

      {/* Floating nodes */}
      <CyberNodes />

      {/* ── Card ── */}
      <div className="relative w-full max-w-md z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-5">
            <div className="relative">
              <img
                src={zainLogo}
                alt="Zain"
                className="h-20 w-20 object-cover rounded-2xl"
                style={{ boxShadow: "0 0 30px rgba(0,255,200,0.3), 0 0 60px rgba(0,255,200,0.1)" }}
              />
              {/* corner accents */}
              <div className="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2 border-cyan-400" />
              <div className="absolute -top-1 -right-1 w-3 h-3 border-t-2 border-r-2 border-cyan-400" />
              <div className="absolute -bottom-1 -left-1 w-3 h-3 border-b-2 border-l-2 border-cyan-400" />
              <div className="absolute -bottom-1 -right-1 w-3 h-3 border-b-2 border-r-2 border-cyan-400" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide">ZainJo LogStream</h1>
          <p className="text-slate-500 text-sm mt-1">Telecom Syslog Management Platform</p>

          {/* security badge */}
          <div className="inline-flex items-center gap-1.5 mt-3 px-3 py-1 rounded-full text-[10px] font-mono tracking-widest"
               style={{ background: "rgba(0,255,200,0.07)", border: "1px solid rgba(0,255,200,0.2)", color: "#00ffcc" }}>
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse inline-block" />
            SECURE CONNECTION ESTABLISHED
          </div>
        </div>

        {/* Login card */}
        <div
          className="rounded-2xl p-8"
          style={{
            background: "rgba(10,14,35,0.85)",
            backdropFilter: "blur(16px)",
            animation: "glowborder 4s ease-in-out infinite",
            position: "relative",
            overflow: "hidden",
          }}
        >
          {/* shimmer stripe */}
          <div
            style={{
              position: "absolute",
              top: 0,
              width: "40%",
              height: "100%",
              background: "linear-gradient(90deg, transparent, rgba(0,255,200,0.04), transparent)",
              animation: "shimmer 5s linear infinite",
              pointerEvents: "none",
            }}
          />

          {/* top bar accent */}
          <div className="absolute top-0 inset-x-0 h-px"
               style={{ background: "linear-gradient(90deg, transparent, #00ffcc, transparent)" }} />

          <h2 className="text-lg font-semibold text-slate-100 mb-6">Sign in to continue</h2>

          {error && (
            <div className="flex items-center gap-2 bg-red-900/30 border border-red-800 rounded-lg px-4 py-3 mb-5 text-red-300 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5 font-mono tracking-wider">
                USERNAME
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyan-600" />
                <input
                  className="input pl-9"
                  style={{ borderColor: "rgba(0,255,200,0.2)", background: "rgba(0,255,200,0.04)" }}
                  type="text"
                  placeholder="admin"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoFocus
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5 font-mono tracking-wider">
                PASSWORD
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyan-600" />
                <input
                  className="input pl-9"
                  style={{ borderColor: "rgba(0,255,200,0.2)", background: "rgba(0,255,200,0.04)" }}
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 mt-2 flex items-center justify-center gap-2 rounded-lg font-medium text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
                color: "white",
                boxShadow: "0 0 20px rgba(99,102,241,0.4)",
              }}
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Authenticating...
                </>
              ) : (
                <>
                  <Lock className="w-4 h-4" />
                  Sign in
                </>
              )}
            </button>
          </form>

          {/* bottom bar accent */}
          <div className="absolute bottom-0 inset-x-0 h-px"
               style={{ background: "linear-gradient(90deg, transparent, #4f46e5, transparent)" }} />
        </div>

        <div className="text-center mt-5 space-y-1">
          <p className="text-slate-600 text-xs font-mono">
            ZainJo LogStream v1.0 — Internal Use Only
          </p>
          <p className="text-slate-700 text-xs">Developed by Eng. Yacoub Smadi</p>
        </div>
      </div>
    </div>
  );
}
