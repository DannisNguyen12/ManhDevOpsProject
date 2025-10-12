# Website Management and Web Crawler API Documentation

## Overview
This API provides comprehensive website monitoring and web crawling capabilities. It includes CRUD operations for managing crawl targets and accessing crawl results, plus crawler management functionality.

## Base URL
```
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}
```

## Endpoints

### Website Management

#### List Websites
Get a list of all monitored websites.

**Request**
```http
GET /websites
```

**Response**
```json
[
    {
        "id": "string",
        "name": "string",
        "url": "string",
        "crawlEnabled": true,
        "crawlInterval": 300,
        "selectors": {
            "title": "title",
            "content": ".content"
        },
        "createdAt": "string",
        "updatedAt": "string"
    }
]
```

#### Create Website
Add a new website to monitor and crawl.

**Request**
```http
POST /websites
Content-Type: application/json

{
    "name": "string",
    "url": "string",
    "crawlEnabled": true,
    "crawlInterval": 300,
    "selectors": {
        "title": "title",
        "content": ".content"
    }
}
```

**Response**
```json
{
    "id": "string",
    "name": "string",
    "url": "string",
    "crawlEnabled": true,
    "crawlInterval": 300,
    "selectors": {
        "title": "title",
        "content": ".content"
    },
    "createdAt": "string",
    "updatedAt": "string"
}
```

#### Get Website
Get details of a specific website.

**Request**
```http
GET /websites/{websiteId}
```

**Response**
```json
{
    "id": "string",
    "name": "string",
    "url": "string",
    "crawlEnabled": true,
    "crawlInterval": 300,
    "selectors": {
        "title": "title",
        "content": ".content"
    },
    "createdAt": "string",
    "updatedAt": "string"
}
```

#### Update Website
Update an existing website configuration.

**Request**
```http
PUT /websites/{websiteId}
Content-Type: application/json

{
    "name": "string",
    "url": "string",
    "crawlEnabled": true,
    "crawlInterval": 300,
    "selectors": {
        "title": "title",
        "content": ".content"
    }
}
```

**Response**
```json
{
    "id": "string",
    "name": "string",
    "url": "string",
    "crawlEnabled": true,
    "crawlInterval": 300,
    "selectors": {
        "title": "title",
        "content": ".content"
    },
    "createdAt": "string",
    "updatedAt": "string"
}
```

#### Delete Website
Remove a website from monitoring.

**Request**
```http
DELETE /websites/{websiteId}
```

**Response**
```
204 No Content
```

### Crawl Results

#### List Crawl Results
Get crawl results with optional filtering.

**Request**
```http
GET /crawl-results?websiteId={websiteId}&startDate={startDate}&endDate={endDate}&limit={limit}
```

**Parameters**
- `websiteId` (optional): Filter by website ID
- `startDate` (optional): Filter results after this date (ISO 8601 format)
- `endDate` (optional): Filter results before this date (ISO 8601 format)
- `limit` (optional): Maximum number of results to return (default: 50, max: 100)

**Response**
```json
[
    {
        "websiteId": "string",
        "timestamp": "string",
        "statusCode": 200,
        "responseTime": 150,
        "contentLength": 1024,
        "title": "Page Title",
        "content": "Extracted content...",
        "error": null
    }
]
```

#### Get Crawl Result
Get a specific crawl result by website ID and timestamp.

**Request**
```http
GET /crawl-results/{resultId}
```

**Response**
```json
{
    "websiteId": "string",
    "timestamp": "string",
    "statusCode": 200,
    "responseTime": 150,
    "contentLength": 1024,
    "title": "Page Title",
    "content": "Extracted content...",
    "error": null
}
```

#### Create Crawl Result
Create a new crawl result (typically called by the crawler Lambda).

**Request**
```http
POST /crawl-results
Content-Type: application/json

{
    "websiteId": "string",
    "timestamp": "string",
    "statusCode": 200,
    "responseTime": 150,
    "contentLength": 1024,
    "title": "Page Title",
    "content": "Extracted content...",
    "error": null
}
```

**Response**
```json
{
    "websiteId": "string",
    "timestamp": "string",
    "statusCode": 200,
    "responseTime": 150,
    "contentLength": 1024,
    "title": "Page Title",
    "content": "Extracted content...",
    "error": null
}
```

#### Delete Crawl Result
Delete a specific crawl result.

**Request**
```http
DELETE /crawl-results/{resultId}
```

**Response**
```
204 No Content
```

### Crawler Management

#### Get Crawler Status
Get the current status and statistics of the web crawler.

**Request**
```http
GET /crawler/status
```

**Response**
```json
{
    "status": "running",
    "lastRun": "2024-01-15T10:30:00Z",
    "nextRun": "2024-01-15T10:35:00Z",
    "activeTargets": 5,
    "totalResults": 1250,
    "successRate": 0.95,
    "averageResponseTime": 245
}
```

#### Start Crawler
Manually trigger the web crawler to run immediately.

**Request**
```http
POST /crawler/start
```

**Response**
```json
{
    "message": "Crawler started successfully",
    "executionId": "string"
}
```

## Error Responses
All endpoints may return the following errors:

```json
{
    "error": "string"
}
```

Status codes:
- 400: Bad Request (invalid input)
- 404: Not Found
- 500: Internal Server Error

## Validation Rules
- Website name is required
- URL must start with http:// or https://
- URL must be valid and accessible
- Crawl interval must be between 60 and 3600 seconds
- Selectors must be valid CSS selectors

## Rate Limiting
- Default limit: 100 requests per minute
- Burst: 200 requests
- Crawler endpoints: 10 requests per minute

## CORS
All endpoints support CORS with the following settings:
- Allowed Origins: *
- Allowed Methods: GET, POST, PUT, DELETE
- Allowed Headers: Content-Type, Authorization