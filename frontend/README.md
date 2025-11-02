# Frontend Module - DoE-Assist

## 概述
DoE-Assist 前端模块基于 React + TypeScript + Material-UI 构建，提供完整的实验参数推荐和预测界面。

## 功能模块

### 1. 用户认证系统
- 用户注册和登录
- JWT Token 认证
- 受保护路由

### 2. 实验参数查询与预测 (/query)
- **分类预测**：判断实验条件好坏（Good/Bad）
- **参数预测**：推荐指定参数的值（基于IQR统计）
- 支持生物分子类型：protein, peptide, polysaccharide
- 支持实验类型：stability, solubility, aggregation
- 8个可选参数输入（pH, temperature, concentration等）
- 显示预测结果、置信度和文献相似度参考

### 3. 文献资料搜索 (/input)
- 根据生物分子名称和实验条件搜索相似文献
- 显示文献相似度评分
- 展示实验参数和结果摘要
- 支持DOI、作者、年份等信息

### 4. CSV批量预测上传 (/upload)
- 上传CSV文件进行批量分类或参数预测
- 分类预测：返回每行结果的Good/Bad判断和置信度
- 参数预测：返回推荐的参数值及范围
- 自动生成下载链接

### 5. 实验历史记录 (/results)
- 查看所有历史预测记录
- 统计：总记录数、良好/较差预测数、平均置信度
- 详情对话框：显示完整预测结果和推荐文献
- 支持按时间排序和筛选

### 6. 用户反馈提交 (/feedback)
- 满意度评分（1-5星）
- 实验类型和功能满意度选择
- 详细文字反馈
- 反馈内容提示

### 7. 首页仪表板 (/dashboard)
- 用户欢迎界面
- 统计数据展示
- 最近实验记录
- 功能入口导航

## Tech Stack
- **React** 18.2+
- **TypeScript** 4.9+
- **Material-UI** 5.15 (组件库)
- **React Router** 6.8 (路由管理)
- **Axios** 1.6 (HTTP客户端)
- **Recharts** 2.8 (数据可视化)
- **Formik + Yup** (表单验证)

## Project Structure
```
frontend/
├── src/
│   ├── components/              # 可复用组件
│   │   ├── ProtectedRoute.tsx       # 受保护路由
│   │   ├── ErrorBoundary.tsx        # 错误边界
│   │   └── Loading.tsx              # 加载组件
│   ├── contexts/                # React Context
│   │   └── AuthContext.tsx          # 认证上下文
│   ├── pages/                   # 页面组件
│   │   ├── HomePage.tsx             # 首页
│   │   ├── LoginPage.tsx            # 登录
│   │   ├── RegisterPage.tsx         # 注册
│   │   ├── WelcomePage.tsx          # 欢迎页
│   │   ├── ParameterQueryPage.tsx   # 参数查询
│   │   ├── DataInputPage.tsx        # 文献搜索
│   │   ├── UploadDatasetPage.tsx    # CSV上传
│   │   ├── ResultsDisplayPage.tsx   # 历史记录
│   │   └── FeedbackPage.tsx         # 反馈
│   ├── services/                # API服务
│   │   ├── api.ts                   # Axios配置
│   │   ├── authService.ts           # 认证服务
│   │   └── experimentService.ts     # 实验服务
│   ├── utils/                   # 工具函数
│   │   ├── formatters.ts            # 格式化工具
│   │   └── validators.ts            # 验证工具
│   ├── config/                  # 配置文件
│   │   └── constants.ts             # 常量配置
│   ├── types/                   # TypeScript类型
│   │   └── index.ts                # 全局类型定义
│   ├── App.tsx                  # 主应用组件
│   └── index.tsx                # 入口文件
├── public/                      # 静态资源
│   ├── index.html                  # HTML模板
│   ├── manifest.json               # PWA清单
│   └── favicon.ico                 # 网站图标
├── Dockerfile                   # 生产构建配置
├── Dockerfile.dev               # 开发环境配置
├── tsconfig.json                # TypeScript配置
├── package.json                 # 依赖配置
└── README.md                    # 说明文档
```

## API 集成

### 后端接口对接
前端完整对接了以下后端API：
- `POST /auth/login` - 用户登录
- `POST /users` - 用户注册
- `POST /api/v1/experiments/predict-classification` - 分类预测
- `POST /api/v1/experiments/predict-parameter` - 参数预测
- `POST /api/v1/predict` - 统一预测接口
- `POST /api/v1/experiments/predict-csv` - CSV批量预测
- `GET /api/v1/experiments/history` - 获取历史记录
- `GET /api/v1/experiments/{id}` - 获取单条记录
- `GET /literature/search` - 搜索文献

## Quick Start

### Using Docker Compose (Recommended)

The easiest way to start the frontend along with the entire system:

```bash
# From project root directory
docker compose up -d --build
```

This will automatically start:
- MySQL database
- Backend API service
- Frontend service (available at http://localhost:3000)

### Local Development (Without Docker)

If you prefer to run the frontend locally:

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The development server will be available at http://localhost:3000

### Production Build

```bash
# Build production version
npm run build

# The build files will be in the `build/` directory
```

## Development Commands
```bash
npm install          # 安装依赖
npm start           # 启动开发服务器 (http://localhost:3000)
npm run build       # 构建生产版本
npm test            # 运行测试
npm run type-check  # TypeScript 类型检查
npm run lint        # ESLint 代码检查
npm run lint:fix    # 自动修复ESLint错误
```

## 环境配置

### Docker Compose Environment
When using Docker Compose, the frontend automatically uses:
- `REACT_APP_API_URL=http://localhost:8000` (configured in docker-compose.yml)

### Local Development Environment
Create `.env` file in the `frontend/` directory (optional):
```env
REACT_APP_API_URL=http://localhost:8000
```

## Docker 部署

### 使用 Docker Compose（推荐）

从项目根目录运行：
```bash
docker compose up -d --build
```

前端服务将自动启动在 http://localhost:3000

### 单独运行前端容器

如果需要单独运行前端容器：

#### 开发环境
```bash
cd frontend
docker build -f Dockerfile.dev -t doe-assist-frontend:dev .
docker run -p 3000:3000 doe-assist-frontend:dev
```

#### 生产环境
```bash
cd frontend
docker build -t doe-assist-frontend:prod .
docker run -p 80:80 doe-assist-frontend:prod
```
访问：http://localhost

## Design Principles
- **响应式设计**：支持桌面和移动设备
- **直观的用户界面**：清晰的导航和反馈
- **实时数据更新**：Loading状态和错误处理
- **良好的用户体验**：表单验证、提示信息、空状态
- **统一的视觉风格**：Material-UI 主题系统

## 主要特性

### 1. 完整的认证流程
- JWT Token 自动管理
- 请求拦截器自动添加Token
- 401错误自动登出
- 受保护的路由重定向

### 2. 丰富的表单交互
- 分类/参数预测切换
- 多选参数预测
- 实时表单验证
- 优雅的错误提示

### 3. 数据可视化
- 历史记录统计卡片
- 文献相似度评分
- 参数范围展示
- 置信度可视化

### 4. 用户体验优化
- Loading状态指示
- 成功/错误反馈
- 空状态提示
- 响应式布局

## 代码质量
- ✅ 无Linter错误
- ✅ TypeScript类型安全
- ✅ 组件化设计
- ✅ 服务层抽象
- ✅ 错误边界处理
- ✅ 工具函数和常用Hooks
- ✅ 统一的常量配置
- ✅ 响应式布局
- ✅ SEO优化
- ✅ PWA支持

## 新增功能与改进

### 工具函数
- **formatters.ts**: 日期、百分比、文件大小等格式化工具
- **validators.ts**: 表单验证和输入校验工具
- **constants.ts**: 统一的常量配置管理

### 自定义Hooks
- **useApi**: 封装API调用逻辑，自动管理loading和error状态
- **useErrorHandler**: 统一的错误处理逻辑

### 通用组件
- **ErrorBoundary**: React错误边界，捕获和处理应用级错误
- **Loading**: 可复用的加载组件

### 类型定义
- **types/index.ts**: 全局TypeScript类型定义

### 配置优化
- **tsconfig.json**: 添加路径别名配置，简化导入路径
- **index.html**: SEO元数据和PWA配置
- **Dockerfile**: 多阶段构建，优化生产部署
- **Dockerfile.dev**: 专用开发环境配置
