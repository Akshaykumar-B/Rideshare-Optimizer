import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { GitCompare, Shield, MapPin, Car } from "lucide-react";
import heroCity from "@/assets/hero-city.png";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store";
import { login, firebaseLogin, seedDemo } from "@/api/client";
import { getAuth, signInWithPopup, GoogleAuthProvider } from "firebase/auth";
import app from "@/lib/firebase";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  
  const navigate = useNavigate();
  const setAuth = useAuthStore((state: any) => state.setAuth);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login(email, password);
      setAuth(res.data.user, res.data.token);
      navigate("/comparison");
    } catch (err: any) {
      setError(err.response?.data?.message || err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError("");
    setLoading(true);
    const auth = getAuth(app);
    const provider = new GoogleAuthProvider();

    try {
      // 1. Authenticate with Firebase via Google Popup
      const result = await signInWithPopup(auth, provider);
      const user = result.user;
      
      // 2. Get the Firebase ID token
      const idToken = await user.getIdToken();

      // 3. Send token to our Flask backend to get our own JWT
      const res = await firebaseLogin(idToken);
      
      // Automatically sets user & token in local storage via the Zustand store.
      setAuth(res.data.user, res.data.token);
      
      // Send to dashboard
      navigate("/comparison");
      
    } catch (err: any) {
      console.error("Login failed", err);
      // Clean up firebase error messages to be user friendly
      const msg = err.response?.data?.message || err.message || "Google Sign-In failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await seedDemo();
      setError("");
      alert("Demo data seeded!");
    } catch (err) {
      setError("Failed to seed demo data.");
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left Hero */}
      <div className="hidden lg:flex w-1/2 bg-slate-950 relative overflow-hidden flex-col items-center justify-center">
        {/* Animated Background Elements */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:14px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-cyan-500/20 blur-[120px] rounded-full delay-700 animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-500/20 blur-[120px] rounded-full animate-pulse" />

        {/* Branding Container at the top/left */}
        <div className="absolute top-8 left-8 xl:top-12 xl:left-12 z-20 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
            <GitCompare className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70 tracking-tight">
            RideShare <span className="text-cyan-400">Optimizer</span>
          </span>
        </div>

        {/* Center Content */}
        <div className="relative z-10 flex flex-col items-center mt-16 w-full max-w-xl px-12">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="w-full relative rounded-2xl overflow-hidden shadow-2xl shadow-cyan-900/40 border border-white/10 bg-white/5 backdrop-blur-md p-4"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-transparent opacity-50" />
            <motion.img
              src={heroCity}
              alt="Smart city route network"
              className="relative z-10 w-full object-cover rounded-xl border border-white/5"
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            />
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.8 }}
            className="mt-12 text-center"
          >
            <h2 className="text-3xl font-bold text-white mb-4 tracking-tight leading-snug">
              Optimize the path of <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 drop-shadow-sm">
                least resistance
              </span>
            </h2>
            <p className="text-slate-400 text-lg max-w-md mx-auto leading-relaxed">
              Compare cutting-edge routing algorithms in real-time and discover the most efficient paths across the city.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Right Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-white dark:bg-slate-950 relative">
        <div className="absolute top-0 right-0 w-full h-full bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-slate-100 via-white to-white dark:from-slate-900 dark:via-slate-950 dark:to-slate-950 -z-10" />

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="w-full max-w-md bg-white dark:bg-slate-900/50 backdrop-blur-xl p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.2)] border border-slate-100 dark:border-white/5"
        >
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Welcome back</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">Sign in to your account</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4 mb-6">
            <div className="space-y-2 text-left">
              <Label htmlFor="email" className="text-slate-700 dark:text-slate-300 font-medium">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-11 bg-slate-50 dark:bg-slate-950/50 border-slate-200 dark:border-slate-800 focus-visible:ring-cyan-500 transition-shadow"
              />
            </div>
            <div className="space-y-2 text-left">
              <div className="flex justify-between items-center">
                <Label htmlFor="password" className="text-slate-700 dark:text-slate-300 font-medium">Password</Label>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11 bg-slate-50 dark:bg-slate-950/50 border-slate-200 dark:border-slate-800 focus-visible:ring-cyan-500 transition-shadow"
              />
            </div>
            
            {error && (
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="p-3 text-sm rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 flex items-center gap-2">
                <Shield className="w-4 h-4" /> {error}
              </motion.div>
            )}

            <Button type="submit" className="w-full h-11 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/25 transition-all duration-300 border-0" size="lg" disabled={loading}>
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
          
          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-slate-200 dark:border-slate-800" />
            </div>
            <div className="relative flex justify-center text-xs uppercase font-medium">
              <span className="bg-white dark:bg-slate-900 px-3 text-slate-500 dark:text-slate-400 rounded-full">Or continue with</span>
            </div>
          </div>

          <div className="space-y-6">
            <Button 
                onClick={handleGoogleLogin} 
                className="w-full h-11 bg-white dark:bg-slate-800 text-slate-700 dark:text-white border border-slate-200 dark:border-slate-700 shadow-sm hover:bg-slate-50 dark:hover:bg-slate-700 transition-all duration-300 flex items-center justify-center gap-3 font-medium" 
                size="lg" 
                disabled={loading}
                type="button"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Google
            </Button>
          </div>

          {/* Seed Button */}
          <div className="mt-8 text-center bg-slate-50 dark:bg-slate-800/30 p-4 rounded-xl border border-slate-100 dark:border-white/5 backdrop-blur-sm">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">Development Access</p>
            <Button type="button" variant="ghost" size="sm" onClick={handleSeed} disabled={seeding} className="w-full text-slate-600 dark:text-slate-300 hover:text-cyan-600 dark:hover:text-cyan-400 hover:bg-cyan-50 dark:hover:bg-cyan-950/30 transition-colors">
              {seeding ? "Seeding Database..." : "🌱 Initialize Base Demo Data"}
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default LoginPage;
