# Qwen v4 Model Download

## HuggingFace 下载失败原因

此前直接通过 HuggingFace 加载 `Qwen/Qwen2.5-1.5B-Instruct` 失败，错误集中在网络连接阶段：

- 无法连接 `https://huggingface.co`
- 本地缓存中没有目标模型文件
- 出现 `WinError 10013` / `WinError 10051`

该失败不是显存问题，也不是 dtype 问题，因为模型尚未进入加载阶段。

## 改用 ModelScope 的原因

当前网络环境访问 HuggingFace 不稳定或被拦截，因此改用 ModelScope 下载模型到本地目录，再通过本地路径进行 smoke test。

## 目标模型

- `Qwen/Qwen2.5-1.5B-Instruct`

## 目标本地目录

- `models/qwen2_5_1_5b_instruct`

## 待填写下载结果

- 下载状态：失败，未成功下载模型权重
- 本地目录：`models/qwen2_5_1_5b_instruct`
- 目录大小：仅有临时目录，未形成完整模型目录
- 关键文件：`config.json`、`tokenizer_config.json`、`tokenizer.json`、`*.safetensors` 均未就绪
- 后续 smoke test：未运行本地模型 smoke test，因为本地目录不完整

## 当前结论

`modelscope` 已安装，下载脚本已创建，并已修复默认缓存/凭据目录写入用户目录导致的权限问题：

- 缓存目录改为：`models/.modelscope_cache`
- 凭据目录改为：`models/.modelscope_credentials`

但实际访问 ModelScope 时仍失败：

- host：`www.modelscope.cn`
- error：`WinError 10013`
- 结论：当前运行环境没有成功获得外网下载权限，模型未下载完成。

下一步建议：

1. 在可访问 ModelScope 的终端手动运行：

```powershell
C:\Users\20112\anaconda3\envs\minimind-lora\python.exe scripts/download_qwen_v4_modelscope.py
```

2. 或手动下载模型文件后放入：

```text
models/qwen2_5_1_5b_instruct
```

3. 确认该目录至少包含：

```text
config.json
tokenizer_config.json
tokenizer.json
*.safetensors
```

4. 再运行本地 smoke test：

```powershell
C:\Users\20112\anaconda3\envs\minimind-lora\python.exe scripts/smoke_test_qwen_v4_model.py --model_name_or_path models/qwen2_5_1_5b_instruct
```

## 下载失败

- model_id：`Qwen/Qwen2.5-1.5B-Instruct`
- target_dir：`E:\Projects\MiniMind-CustomerService-LoRA\models\qwen2_5_1_5b_instruct`
- error：`PermissionError: [WinError 5] 拒绝访问。: 'C:\\Users\\20112\\.cache\\modelscope'`

```text
Traceback (most recent call last):
  File "E:\Projects\MiniMind-CustomerService-LoRA\scripts\download_qwen_v4_modelscope.py", line 74, in main
    snapshot_download(
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\modelscope\hub\snapshot_download.py", line 138, in snapshot_download
    os.makedirs(os.path.join(system_cache, '.lock'), exist_ok=True)
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\os.py", line 215, in makedirs
    makedirs(head, exist_ok=exist_ok)
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\os.py", line 215, in makedirs
    makedirs(head, exist_ok=exist_ok)
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\os.py", line 225, in makedirs
    mkdir(name, mode)
PermissionError: [WinError 5] 拒绝访问。: 'C:\\Users\\20112\\.cache\\modelscope'

```

## 下载失败

- model_id：`Qwen/Qwen2.5-1.5B-Instruct`
- target_dir：`E:\Projects\MiniMind-CustomerService-LoRA\models\qwen2_5_1_5b_instruct`
- error：`PermissionError: [WinError 5] 拒绝访问。: 'C:/Users/20112/.modelscope'`

```text
Traceback (most recent call last):
  File "E:\Projects\MiniMind-CustomerService-LoRA\scripts\download_qwen_v4_modelscope.py", line 81, in main
    snapshot_download(
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\modelscope\hub\snapshot_download.py", line 145, in snapshot_download
    return _snapshot_download(
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\modelscope\hub\snapshot_download.py", line 307, in _snapshot_download
    ModelScopeConfig.get_user_agent(user_agent=user_agent, ),
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\modelscope\hub\api.py", line 4172, in get_user_agent
    ModelScopeConfig.get_user_session_id(),
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\modelscope\hub\api.py", line 4090, in get_user_session_id
    ModelScopeConfig.make_sure_credential_path_exist()
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\modelscope\hub\api.py", line 4050, in make_sure_credential_path_exist
    os.makedirs(ModelScopeConfig.path_credential, exist_ok=True)
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\os.py", line 215, in makedirs
    makedirs(head, exist_ok=exist_ok)
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\os.py", line 225, in makedirs
    mkdir(name, mode)
PermissionError: [WinError 5] 拒绝访问。: 'C:/Users/20112/.modelscope'

```

## 下载失败

- model_id：`Qwen/Qwen2.5-1.5B-Instruct`
- target_dir：`E:\Projects\MiniMind-CustomerService-LoRA\models\qwen2_5_1_5b_instruct`
- error：`ConnectionError: HTTPSConnectionPool(host='www.modelscope.cn', port=443): Max retries exceeded with url: /api/v1/models/Qwen/Qwen2.5-1.5B-Instruct (Caused by NewConnectionError("HTTPSConnection(host='www.modelscope.cn', port=443): Failed to establish a new connection: [WinError 10013] 以一种访问权限不允许的方式做了一个访问套接字的尝试。"))`

```text
Traceback (most recent call last):
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\urllib3\connection.py", line 204, in _new_conn
    sock = connection.create_connection(
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\urllib3\util\connection.py", line 85, in create_connection
    raise err
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\urllib3\util\connection.py", line 73, in create_connection
    sock.connect(sa)
PermissionError: [WinError 10013] 以一种访问权限不允许的方式做了一个访问套接字的尝试。

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\urllib3\connectionpool.py", line 788, in urlopen
    response = self._make_request(
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\urllib3\connectionpool.py", line 488, in _make_request
    raise new_e
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\urllib3\connectionpool.py", line 464, in _make_request
    self._validate_conn(conn)
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\urllib3\connectionpool.py", line 1106, in _validate_conn
    conn.connect()
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\urllib3\connection.py", line 759, in connect
    self.sock = sock = self._new_conn()
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\urllib3\connection.py", line 219, in _new_conn
    raise NewConnectionError(
urllib3.exceptions.NewConnectionError: HTTPSConnection(host='www.modelscope.cn', port=443): Failed to establish a new connection: [WinError 10013] 以一种访问权限不允许的方式做了一个访问套接字的尝试。

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\requests\adapters.py", line 696, in send
    resp = conn.urlopen(
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\urllib3\connectionpool.py", line 872, in urlopen
    return self.urlopen(
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\urllib3\connectionpool.py", line 872, in urlopen
    return self.urlopen(
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\urllib3\connectionpool.py", line 842, in urlopen
    retries = retries.increment(
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\urllib3\util\retry.py", line 543, in increment
    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='www.modelscope.cn', port=443): Max retries exceeded with url: /api/v1/models/Qwen/Qwen2.5-1.5B-Instruct (Caused by NewConnectionError("HTTPSConnection(host='www.modelscope.cn', port=443): Failed to establish a new connection: [WinError 10013] 以一种访问权限不允许的方式做了一个访问套接字的尝试。"))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "E:\Projects\MiniMind-CustomerService-LoRA\scripts\download_qwen_v4_modelscope.py", line 94, in main
    snapshot_download(
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\modelscope\hub\snapshot_download.py", line 145, in snapshot_download
    return _snapshot_download(
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\modelscope\hub\snapshot_download.py", line 323, in _snapshot_download
    endpoint = _api.get_endpoint_for_read(
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\modelscope\hub\api.py", line 625, in get_endpoint_for_read
    if not self.repo_exists(
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\modelscope\hub\api.py", line 782, in repo_exists
    r = self.session.get(path, cookies=cookies,
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\requests\sessions.py", line 671, in get
    return self.request("GET", url, params=params, **kwargs)
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\requests\sessions.py", line 651, in request
    resp = self.send(prep, **send_kwargs)
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\requests\sessions.py", line 784, in send
    r = adapter.send(request, **kwargs)
  File "C:\Users\20112\anaconda3\envs\minimind-lora\lib\site-packages\requests\adapters.py", line 729, in send
    raise ConnectionError(e, request=request)
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='www.modelscope.cn', port=443): Max retries exceeded with url: /api/v1/models/Qwen/Qwen2.5-1.5B-Instruct (Caused by NewConnectionError("HTTPSConnection(host='www.modelscope.cn', port=443): Failed to establish a new connection: [WinError 10013] 以一种访问权限不允许的方式做了一个访问套接字的尝试。"))

```

## 手动下载成功更新

后续模型已成功放置到本地路径：

- local_dir：`models/qwen2_5_1_5b_instruct`
- smoke test：成功
- dtype：bfloat16
- CUDA memory after load：2.875 GB allocated / 2.930 GB reserved
- CUDA memory after generation：2.907 GB allocated / 2.936 GB reserved

当前可直接通过本地路径加载模型，无需再次从 HuggingFace 或 ModelScope 下载。

## 下载结果

- model_id：`Qwen/Qwen2.5-1.5B-Instruct`
- local_dir：`E:\Projects\MiniMind-CustomerService-LoRA\models\qwen2_5_1_5b_instruct`
- status：success
- directory_size_gb：2.886
- key_files：

```json
{
  "config.json": true,
  "tokenizer_config.json": true,
  "tokenizer.json": true,
  "vocab.json": true,
  "merges.txt": true,
  "safetensors": [
    "model.safetensors"
  ]
}
```
