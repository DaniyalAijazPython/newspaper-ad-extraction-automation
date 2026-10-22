# Newspaper Advertisement Extraction & Automation

An automated Python-based system that collects newspaper pages, detects advertisements, extracts structured property information using Optical Character Recognition (OCR), and stores the results in a PostgreSQL database.

The project also provides a REST API built with FastAPI to retrieve and filter collected advertisements.

## Project Overview

This project explores how newspaper advertisement processing can be automated using Python, computer vision, OCR, and database technologies.

The system is designed around Dawn ePaper and focuses on extracting property-related advertisement information from newspaper images.

## Key Features

- Newspaper edition discovery and image downloading
- Image processing and text recognition using OpenCV and Tesseract OCR
- Newspaper column detection and advertisement segmentation
- Extraction of phone numbers, locations, bedrooms, property types, and transaction types
- Structured advertisement storage in PostgreSQL
- Duplicate advertisement handling
- REST API with filtering and pagination
- Automated pipeline execution and logging
- Automated testing using Pytest

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3 | Core programming language |
| OpenCV | Image processing and advertisement detection |
| Tesseract OCR | Text recognition |
| Pillow | Image handling |
| FastAPI | REST API development |
| PostgreSQL | Database |
| SQLAlchemy | Database ORM |
| Alembic | Database migrations |
| Pytest | Automated testing |

## Project Structure

```text
Newspaper_project/
├── collector/
│   ├── dawn.py
│   ├── image_extractor.py
│   ├── ocr_extractor.py
│   ├── ad_detector.py
│   ├── data_extractor.py
│   └── pipeline.py
├── Database/
│   └── db.py
├── models/
│   └── advertisements.py
├── router/
│   └── advertisements.py
├── schema/
│   └── advertisements.py
├── service/
│   └── advertisement_service.py
├── config/
│   └── setting.py
├── alembic/
├── test/
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

## How the Pipeline Works

1. Discover advertisement-related pages from the newspaper edition.
2. Download the relevant newspaper images.
3. Process the images and recognize text using OCR.
4. Group detected text into newspaper columns and advertisement candidates.
5. Extract structured information from the recognized text.
6. Store advertisement records in PostgreSQL.
7. Make the stored information accessible through the FastAPI application.

## Installation

Clone the repository:

```bash
git clone https://github.com/DaniyalAijazPython/newspaper-ad-extraction-automation.git
cd newspaper-ad-extraction-automation
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Tesseract OCR and PostgreSQL must also be installed separately.

Configure the required environment variables, including the database connection string, in a local `.env` file. Do not commit credentials to GitHub.

Run database migrations:

```bash
alembic upgrade head
```

## Running the Project

Start the newspaper processing pipeline:

```bash
python -m collector.pipeline
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

Open the interactive API documentation:

`http://127.0.0.1:8000/docs`

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API home endpoint |
| GET | `/advertisements/` | Retrieve advertisements |
| GET | `/advertisements/{advertisement_id}` | Retrieve a specific advertisement |
| GET | `/advertisements/stats` | Advertisement statistics |

The advertisement listing endpoint supports filtering and pagination.

## Testing

Run all automated tests:

```bash
python -m pytest -v
```

The project includes tests for API behavior, pipeline failure handling, and structured data extraction.

## Current Limitations

- OCR accuracy depends on newspaper image quality.
- Advertisement segmentation may require adjustments for different newspaper layouts.
- Location extraction currently uses predefined location patterns.
- Some advertisements may contain incomplete or incorrectly recognized information.
- The pipeline has been tested locally; production VPS deployment is a future step.

## Future Improvements

- Improve OCR and advertisement segmentation accuracy
- Support additional newspaper layouts
- Add advanced data validation and extraction methods
- Build an analytics dashboard
- Deploy the pipeline and API to a cloud server

## Author

Developed by **Daniyal Aijaz** as a Python automation, computer vision, and backend development project.

## Project Status

**Local development and GitHub publication stage.** Production deployment is planned for a future release.
