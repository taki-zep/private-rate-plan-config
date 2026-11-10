# 接口文档：获取 Dolphin 配置

## 请求

### HTTP
```
GET http://wolf-v3-api.didainternal.com:8081/public/api/dolphin/config/{traceId}/{bizTier}/{key}
Authorization: Bearer <token>
```

### HTTP示例
```
GET http://wolf-v3-api.didainternal.com:8081/public/api/dolphin/config/2026072011233123/40/SS.SupplierRateLimit.Config
Authorization: Bearer <token>
```

### Headers

| Header | 必填 | 类型 | 说明 |
|---|---|---|---|
| `Authorization` | 是 | string | 鉴权令牌，格式 `Bearer <token>`|

### Path 参数

| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `traceId` | 是 | string | 调用方传入的链路 ID，用于排障日志串联。服务端**仅记录到错误日志**，不参与业务校验 |
| `bizTier` | 是 | string | Dolphin 业务层级。允许值见下表 |
| `key` | 是 | string | Dolphin 中的配置 key |

### `bizTier` 允许值

| value | 枚举名 |
|---|---|
| `10` | Framework |
| `20` | CoreBiz |
| `30` | Channel |
| `40` | Supplier |
| `50` | System |
| `60` | Tool |
| `70` | Manager |
| `80` | Job |
| `9999` | Test |

传入其它值时返回失败 `"BizTier不存在"`。

---

## 响应

统一响应体 `StandardResponseModel<String>`，结构如下：

| 字段 | 类型 | 说明 |
|---|---|---|
| `success` | boolean | `true` 表示业务成功，`false` 表示业务失败 |
| `message` | string | 提示消息 |
| `messageCode` | integer | 成功固定 `20000`，失败固定 `50000` |
| `data` | string \| null | 配置原始值；key 存在时为对应的value，key 不存在时为 `null` |

### 成功响应（HTTP 200，业务成功）

#### 场景 A：key 存在

```json
{
  "success": true,
  "message": "success",
  "messageCode": 20000,
  "data": "{\"connectTimeout\":3000,\"readTimeout\":5000}"
}
```

#### 场景 B：key 在 Dolphin 中不存在

```json
{
  "success": true,
  "message": "success",
  "messageCode": 20000,
  "data": null
}
```

### 失败响应（HTTP 200，业务失败）

所有失败情况 `success=false`、`messageCode=50000`，HTTP 状态码仍为 200。

| 失败 message | 触发条件 |
|---|---|
| `"authorization 不能为空"` | 请求未带 `Authorization` 头，或值为空白 |
| `"authorization 不合法"` | Authorization 不在 允许列表中|
| `"BizTier不存在"` | `bizTier` 不是 `BizTier` 枚举允许的 value |
| `"QPS过高, 触发限流"` | Sentinel 流控规则命中 |
| `"触发其他Sentinel规则:" + e.getMessage()` | Sentinel 其他规则命中（降级 / 系统 / 授权等 ） |
| `e.getMessage()` | 其它运行时异常（如 Dolphin 调用失败） |

#### 失败响应示例

```json
{
  "success": false,
  "message": "authorization 不合法",
  "messageCode": 50000,
  "data": null
}
```

```json
{
  "success": false,
  "message": "QPS过高, 触发限流",
  "messageCode": 50000,
  "data": null
}
```