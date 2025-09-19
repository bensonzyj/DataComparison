# DataComparison

业务数据提取比对平台原型，演示如何基于模板驱动的 OCR/文本抽取流程，将线下凭证中的核心业务字段与系统内数据进行自动比对。

## 功能概览
- 模板化字段定义：通过 `datacomparison/templates/*.json` 管理不同文档类型的提取与比对策略（可扩展至 YAML）。
- 文档解析：支持文本、PDF、Word、图片（OCR）等多种格式的解析封装，可按需扩展。
- 字段抽取：当前内置正则策略，可扩展为版面定位、深度学习模型抽取。
- 数据比对：提供精确匹配、模糊匹配、数值、日期等策略，并输出差异说明与置信度。
- API 接口：基于 FastAPI 暴露 `/compare`、`/templates/{id}` 等服务接口。

## 目录结构
```
.
├── datacomparison
│   ├── api.py               # FastAPI 应用
│   ├── config.py            # 全局配置
│   ├── services             # 解析/抽取/比对核心逻辑
│   ├── templates            # 模板配置
│   └── utils                # 归一化等工具函数
├── docs
│   └── architecture.md      # 系统架构设计说明
├── tests                    # 单元测试
└── README.md
```

## 快速开始
1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
   > OCR、PDF、Word 等解析依赖（`pytesseract`、`pdfplumber`、`python-docx` 等）为可选项，按需安装。

2. 运行 API 服务：
   ```bash
   uvicorn datacomparison.api:app --reload
   ```

3. 发起比对请求（示例）：
   ```bash
   curl -X POST http://localhost:8000/compare \
     -H "Content-Type: application/json" \
     -d '{
       "template_id": "promise_letter",
       "system_data": {
         "customer_name": "张三",
         "id_number": "110101199001011234",
         "amount": "100000.00",
         "signing_date": "2024-05-20"
       },
       "document_text": "承诺书\n姓名：张三\n身份证号：110101199001011234\n金额：100,000.00\n日期：2024-05-20"
     }'
   ```

## 测试
```bash
pytest
```

## 扩展方向
- 接入 PaddleOCR/Donut 等模型提升复杂版面抽取效果。
- 增加模板管理界面、人工复核工作流和审计日志。
- 引入 Celery 等异步框架支持批量任务处理。
