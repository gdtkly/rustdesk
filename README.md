# 连连控远程 · 品牌化客户端构建套件

把 RustDesk **1.4.9** 源码编译成一个完全改名、换图标、换主色、并且**开箱即连你自己服务器**的 Windows 安装包。

- 服务器：`120.79.178.237`（hbbs 21116 / hbbr 21117 / ws 21118-21119）
- 服务端公钥：已写入客户端，用户不需要手动填
- 产品名：**连连控远程**（窗口标题、安装目录、快捷方式、控制面板卸载项、界面文案全部跟着变）

产物是两个文件：

| 文件 | 用途 |
|---|---|
| `连连控远程_v1.4.9_x64_安装包.exe` | 双击安装版，装到 `C:\Program Files\连连控远程\` |
| `连连控远程_v1.4.9_x64_绿色版.zip` | 免安装，解压即用 |

---

## 一、目录说明

```
llk-client/
├── brand.json                        ← 品牌配置，改这里就行
├── .github/workflows/
│   └── build-llk-windows.yml         ← 云端构建流水线
├── branding/
│   ├── apply_branding.py             ← 品牌化补丁（改源码）
│   └── assets/                       ← 图标 / LOGO 全部资源
│       ├── res/                      ← 程序图标（ico/png/svg）
│       ├── flutter/                  ← 界面内 LOGO
│       ├── runner/app_icon.ico       ← 最终 exe 的图标
│       └── portable/label.png        ← 安装器窗口上的小标
└── tools/make_assets.py              ← 重新生成图标（换 LOGO 时用）
```

---

## 二、三步出包

### 第 1 步：Fork 源码

打开 https://github.com/rustdesk/rustdesk ，右上角 **Fork**，创建一个属于你的仓库。
（必须是 fork，因为流水线要用仓库自带的 `bridge.yml` 等文件生成绑定代码。）

### 第 2 步：把本套件放进 fork 的根目录

把 `brand.json`、`.github/`、`branding/` 三个东西上传到 fork 根目录（网页上 **Add file → Upload files** 直接拖进去即可，注意保持 `.github/workflows/` 的层级不要变）。

用命令行的方式：

```bash
git clone https://github.com/<你的用户名>/rustdesk
cd rustdesk
# 把 llk-client 目录里的 brand.json、.github、branding 复制进来
git add brand.json branding .github/workflows/build-llk-windows.yml
git commit -m "feat: 连连控远程品牌化构建"
git push
```

### 第 3 步：触发构建

仓库页面 → **Actions** → 左侧选 **构建连连控远程-Windows** → **Run workflow**。

| 阶段 | 耗时 |
|---|---|
| 生成 bridge 绑定 | 8-15 分钟 |
| 编译 TopMostWindow 组件 | 2-3 分钟 |
| 编译主程序 + 打包 | 30-50 分钟 |

跑完在运行记录页面底部 **Artifacts** 下载 `连连控远程-Windows-x64`。

---

## 三、改品牌 / 换 LOGO

### 改文字和服务器

编辑 `brand.json`：

| 字段 | 现在填的 | 说明 |
|---|---|---|
| `app_name` | 连连控远程 | 应用名，会决定窗口标题和安装目录 |
| `company_name` | 丰顺成大网络科技有限公司 | 会写进 exe 属性和卸载列表 |
| `copyright` | Copyright © 2026 丰顺成大网络科技有限公司 版权所有 | exe 属性里的版权 |
| `brand_color` | #0FA968 | 界面主色 |
| `server_ip` | 120.79.178.237 | 自建服务器地址 |
| `server_key` | CA1z+gwX... | 服务端公钥，来自 `/root/id_ed25519.pub` |

改完重新 Run workflow 即可，不用碰源码。

### 换正式 LOGO

当前 LOGO 是随本套件设计的：**渐变绿圆角方块 + 白色鼠标指针**（指针＝操控，方块＝桌面窗口），所有尺寸由 `tools/make_assets.py` 里的 `_CURSOR_RAW` / `MARK_SIZE` / `RADIUS_RATIO` / `brand_color` 参数控制，改参数就能微调造型。

换成你自己的 LOGO，二选一：

1. **自动生成全套尺寸**：把 `brand.json` 的 `logo_source` 填成图片路径，然后
   ```bash
   pip install pillow
   python tools/make_assets.py
   ```
   会把 16~1024 所有尺寸、多尺寸 ico、界面内横向 LOGO 全部重新生成。
2. **手工替换**：直接覆盖 `branding/assets/` 下对应文件（`res/icon.ico` 建议包含 16/32/48/256 多尺寸）。

### 界面配色

`brand_color` 会同时改掉 `flutter/lib/common.dart` 里的 `accent` / `accent50` / `accent80` / `button` / `idColor`。

---

## 四、这套补丁到底改了哪里

`branding/apply_branding.py` 每次构建都会执行，改 22 处：

| 位置 | 改什么 |
|---|---|
| `libs/hbb_common/src/config.rs` | `APP_NAME` 改成 连连控远程；`RENDEZVOUS_SERVERS` 写死你的 IP；`RS_PUB_KEY` 换成你的公钥 |
| `flutter/windows/runner/Runner.rc` | exe 属性：公司名、产品名、描述、版权，并把代码页切成 Unicode，中文不乱码 |
| `Cargo.toml` | winres / macOS bundle 元信息 |
| `libs/portable/Cargo.toml` | 安装器 EXE 自身的属性 |
| `flutter/lib/common.dart` | 主色 |
| `res/`、`flutter/assets/`、`runner/resources/`、`portable/src/res/` | 图标与 LOGO |

界面里所有出现 "RustDesk" 的文案，会被 `src/lang.rs` 的机制自动替换成 `APP_NAME`——这是 RustDesk 给自建用户留的官方口子，所以不用一条条改翻译文件。

任何一处没匹配上，脚本会直接报错中止构建，不会出现"编出来了但还是 RustDesk"的情况。

---

## 五、需要知道的几个限制

1. **exe 内部文件名仍叫 `rustdesk.exe`**（在 `C:\Program Files\连连控远程\` 里）。外壳名称、图标、属性、快捷方式全是"连连控远程"，但任务管理器里进程名会是 rustdesk.exe。要彻底改需要连服务、自启动注册一起动，容易引入难查的 bug，建议保持。
2. **服务器地址是编译期写死的**，用户在"设置→网络"里仍可改成别的地址（RustDesk 的设计如此）。
3. **没有代码签名证书**，用户首次运行会被 SmartScreen 拦一下（"更多信息→仍要运行"）。要做正式分发，建议买一张 OV/EV 代码签名证书，在流水线里加 `signtool` 签名步骤。
4. **许可**：RustDesk 是 AGPL-3.0。自用没问题；如果要**对外分发**（给客户装），需要按 AGPL 提供对应源码（比如把这个 fork 保持公开）。

---

## 六、出问题怎么查

| 现象 | 原因 |
|---|---|
| 卡在 `apply_branding.py` 报"未匹配到目标内容" | 你用的不是 1.4.9 源码，正则要跟着调 |
| vcpkg 那步失败 | 网络拉 ffmpeg 依赖超时，重跑一次 |
| `flutter build windows` 报 bridge 相关错误 | bridge artifact 没还原成功，检查第一个 job 是否成功 |
| 装完了连不上 | 检查服务器 21116/21117 是否放行 UDP，以及客户端 KEY 是否与 `id_ed25519.pub` 一致 |

---

## 七、验证过的信息（本套件制作时实测）

- 你的 KEY 解码后是 32 字节 ed25519 公钥，格式正确
- `120.79.178.237` 的 21115/21116/21117/21118/21119 均可连通
- 21114 未开放 → 你跑的是 **Server 开源版**，所以官方 Pro 的"自定义客户端生成器"用不了，只能走源码编译这条路
