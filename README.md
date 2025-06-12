

# Dynamic OG Image System

A FastAPI-based service for **dynamic Open Graph image generation** used for news articles. It is optimized for performance, caching, and supports extensibility with templates.

---

## Features

* 🔹 Dynamic OG image generation for:

  * News articles
* 🖼️ Caching support:

  * Memory, Disk, or S3
  * Cache-control headers for CDN
* 🚀 Ready for:

  * Docker & Docker Compose
  * AWS ECS/EKS deployments

---

## Tech Stack

* Python 3.11 + FastAPI
* Pillow (PIL) for image rendering
* MongoDB (for metadata)
* AWS S3 (optional) for remote caching
* OpenTelemetry for observability
* Docker for containerization

---

## Endpoints

```http
GET /og/news/{slug}     → News article card  
```

Each endpoint accepts dynamic data and returns a `.webp` OG image, ready to be embedded in social shares.

---

## Running Locally

```bash
git clone https://github.com/Ayush-pbh/dynamic-og-service.git
cd dynamic-og-service

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 3000
```

Then visit: `http://localhost:3000/og/news/sample-slug`


---

## Cache Support

This service supports pluggable caching strategies:

* `NONE` – always regenerate
* `DISK` – cache locally in `/generated`
* `S3` – upload to S3, and optionally serve via CloudFront

🌀 CloudFront or any CDN can cache OG images by respecting
`Cache-Control: max-age=31536000` — enabling global edge delivery.

---

## Contribution

This repo is maintained by **Ayush Tripathi** 
