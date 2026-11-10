### Wolf V2 根据机构 id 和配置 key 获取配置信息

请求

```bash
curl -X POST 'https://wolf-caller-api.didaadmin.com/api/v1/ClientConfigurations/GetConfigurationValueByClientIdAndKey' \
  --header 'Accept: */*' \
  --header 'Content-Type: application/json' \
  --data '{
  "clientIds": [
    "A__map"
  ],
  "configurationKeys": [
    "EnableDidaRoomName",
    "PriceSearchCachePPS"
  ]
}'
```

| 参数              | 类型  | 描述     |
| ----------------- | ----- | -------- |
| clientIds         | Array | 机构 id  |
| configurationKeys | Array | 配置 key |

响应

```json
{
  "message": "success",
  "success": true,
  "messageCode": 20000,
  "data": [
    {
      "clientId": "A__map",
      "configurationValues": [
        {
          "configurationKey": "PriceSearchCachePPS",
          "configurationValue": "2000",
          "defaultValue": "200"
        },
        {
          "configurationKey": "EnableDidaRoomName",
          "configurationValue": null,
          "defaultValue": "true"
        }
      ]
    }
  ]
}
```

| **参数**                                        | **类型**       | **描述**                      |
| ----------------------------------------------- | -------------- | ----------------------------- |
| message                                         | String         | 响应消息                      |
| success                                         | Boolean        | 请求是否成功                  |
| messageCode                                     | Integer        | 响应状态码                    |
| data                                            | Array          | 数据列表                      |
| data[].clientId                                 | String         | 机构 id                       |
| data[].configurationValues                      | Array          | 配置项列表                    |
| data[].configurationValues[].configurationKey   | String         | 配置 key                      |
| data[].configurationValues[].configurationValue | String \| Null | 当前配置值；未配置时为 `null` |
| data[].configurationValues[].defaultValue       | String         | 配置项默认值                  |

### ⚠️注意⚠️

当配置值为 `null`，但有默认值时，默认行为会返回配置的默认值

比如 `ClientConfigurationCaller.GetRawValue("A__map", "EnableDidaRoomName")`

在调用时虽然 `configurationValue = null` 但是会返回 `true`，除非显式指定 `useDefault = false`

比如：

```c#
ClientConfigurationCaller.GetRawValue("A__map", "EnableDidaRoomName", useDefault:false)
```

此时当 `EnableDidaRoomName` 配置为 `null` 时，即使有默认值也会返回 `null`