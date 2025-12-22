import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    
    return {
      server: {
        port: 3000,
        host: '0.0.0.0',
        // 代理配置：通过环境变量 HTTP_PROXY 和 HTTPS_PROXY 自动使用代理
        // 这些环境变量在 package.json 的 dev 脚本中已设置
        proxy: {
          // 如果需要，可以在这里添加特定的代理规则
          // 环境变量 HTTP_PROXY=http://127.0.0.1:7899 会自动应用到所有代理请求
        },
      },
      plugins: [react()],
      // 已移除 GEMINI_API_KEY 定义，现在通过后端 API 调用
      // 前端不再需要直接访问 Gemini API
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      }
    };
});
