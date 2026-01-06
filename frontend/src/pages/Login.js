import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { LogIn, Mail, Lock, Heart, Shield, Sparkles } from 'lucide-react';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      console.log('Submitting login form...');
      const result = await login(formData.email, formData.password);
      console.log('Login result:', result);
      
      if (result.success) {
        toast.success('Welcome back!');
        navigate('/');
      } else {
        console.error('Login failed:', result.error);
        toast.error(result.error || 'Login failed');
      }
    } catch (error) {
      console.error('Login exception:', error);
      toast.error('An error occurred during login: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen healthcare-pattern flex items-center justify-center p-4">
      {/* Animated background */}
      <div className="animated-bg"></div>
      
      {/* Floating healthcare icons */}
      <div className="absolute top-20 left-20 opacity-10 text-teal-500 healthcare-float" style={{animationDelay: '0s'}}>
        <Heart size={48} />
      </div>
      <div className="absolute bottom-32 right-24 opacity-10 text-purple-500 healthcare-float" style={{animationDelay: '2s'}}>
        <Shield size={56} />
      </div>
      <div className="absolute top-40 right-32 opacity-10 text-teal-400 healthcare-float" style={{animationDelay: '4s'}}>
        <Sparkles size={40} />
      </div>
      
      <div className="relative w-full max-w-md">
        {/* Gradient border effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-teal-500 via-purple-500 to-cyan-500 rounded-2xl blur-sm opacity-50"></div>
        
        <div className="relative glass-card rounded-2xl overflow-hidden">
          {/* Header */}
          <div className="p-8 text-center border-b border-white/10">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 rounded-2xl gradient-teal flex items-center justify-center glow-teal">
                <Heart className="text-white" size={32} />
              </div>
            </div>
            <h1 className="text-3xl font-bold gradient-text mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              AZAI Health
            </h1>
            <p className="text-gray-400">Sign in to your healthcare dashboard</p>
          </div>
          
          {/* Form */}
          <div className="p-8">
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <Label htmlFor="email" className="flex items-center gap-2 text-gray-300 mb-2">
                  <Mail size={16} className="text-teal-400" />
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="your@email.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  className="modern-input"
                />
              </div>

              <div>
                <Label htmlFor="password" className="flex items-center gap-2 text-gray-300 mb-2">
                  <Lock size={16} className="text-teal-400" />
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  className="modern-input"
                />
              </div>

              <button
                type="submit"
                className="w-full btn-primary py-3 text-lg font-semibold flex items-center justify-center gap-2 mt-6"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    Signing In...
                  </>
                ) : (
                  <>
                    <LogIn size={20} />
                    Sign In
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-400">
                Don't have an account?{' '}
                <Link to="/signup" className="text-teal-400 hover:text-teal-300 font-semibold transition-colors">
                  Sign Up
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
