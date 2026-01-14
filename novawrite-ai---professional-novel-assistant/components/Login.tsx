import React, { useEffect, useState } from 'react';
import { LogIn, Lock, RefreshCw, Shield, User } from 'lucide-react';
import { checkLoginStatus, getCaptcha, login } from '../services/authService';

interface LoginProps {
  onLoginSuccess: () => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [captchaCode, setCaptchaCode] = useState('');
  const [captchaId, setCaptchaId] = useState('');
  const [captchaImage, setCaptchaImage] = useState('');
  const [requiresCaptcha, setRequiresCaptcha] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingCaptcha, setLoadingCaptcha] = useState(false);
  const [error, setError] = useState('');

  // 加载验证码
  const loadCaptcha = async () => {
    setLoadingCaptcha(true);
    try {
      const captcha = await getCaptcha();
      setCaptchaId(captcha.captcha_id);
      setCaptchaImage(captcha.image);
      setCaptchaCode(''); // 清空验证码输入
    } catch (err) {
      console.error('加载验证码失败', err);
    } finally {
      setLoadingCaptcha(false);
    }
  };

  // 检查登录状态（是否需要验证码）
  const checkStatus = async () => {
    if (!username.trim()) return;

    try {
      const status = await checkLoginStatus(username);
      setRequiresCaptcha(status.requires_captcha);

      if (status.locked) {
        setError(status.lock_message || '账号已被锁定');
        return;
      }

      if (status.requires_captcha && !captchaId) {
        await loadCaptcha();
      }
    } catch (err) {
      // 忽略检查状态错误
    }
  };

  // 当用户名改变时检查状态
  useEffect(() => {
    if (!username.trim()) {
      setRequiresCaptcha(false);
      setCaptchaId('');
      setCaptchaImage('');
      return;
    }

    const timer = setTimeout(() => {
      checkStatus();
    }, 500);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [username]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (requiresCaptcha && !captchaCode.trim()) {
      setError('请输入验证码');
      return;
    }

    setLoading(true);

    try {
      await login(
        username,
        password,
        requiresCaptcha ? captchaId : undefined,
        requiresCaptcha ? captchaCode : undefined
      );
      onLoginSuccess();
    } catch (err: any) {
      const errorMessage = err?.message || '登录失败，请重试';
      setError(errorMessage);

      if (errorMessage.includes('验证码') || errorMessage.includes('需要')) {
        setRequiresCaptcha(true);
        await loadCaptcha();
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-full mb-4">
              <User className="text-white" size={32} />
            </div>
            <h1 className="text-3xl font-bold text-slate-800 mb-2">智能小说写作助手</h1>
            <p className="text-slate-500">登录您的账号</p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">用户名</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="请输入用户名"
                  required
                  className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">密码</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="请输入密码"
                  required
                  minLength={1}
                  className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                />
              </div>
            </div>

            {requiresCaptcha && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">验证码</label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Shield className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
                    <input
                      type="text"
                      value={captchaCode}
                      onChange={(e) => setCaptchaCode(e.target.value.toUpperCase())}
                      placeholder="请输入验证码"
                      required
                      maxLength={4}
                      className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none uppercase"
                    />
                  </div>
                  <div className="flex items-center">
                    {captchaImage ? (
                      <div className="relative">
                        <img
                          src={captchaImage}
                          alt="验证码"
                          className="h-10 w-28 border border-slate-300 rounded cursor-pointer"
                          onClick={loadCaptcha}
                          title="刷新验证码"
                        />
                        <button
                          type="button"
                          onClick={loadCaptcha}
                          disabled={loadingCaptcha}
                          className="absolute -right-8 top-0 p-1 text-slate-500 hover:text-indigo-600 transition-colors"
                          title="刷新验证码"
                        >
                          <RefreshCw size={16} className={loadingCaptcha ? 'animate-spin' : ''} />
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={loadCaptcha}
                        disabled={loadingCaptcha}
                        className="px-3 py-2.5 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors text-sm"
                      >
                        {loadingCaptcha ? '加载中...' : '获取验证码'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              <LogIn size={18} />
              {loading ? '登录中...' : '登录'}
            </button>
          </form>
        </div>

        <div className="mt-6 text-center text-sm text-slate-500">
          <p>提示：数据存储在浏览器本地，请妥善保管您的账号信息。</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
