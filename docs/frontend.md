# Frontend Architecture

## Purpose
The frontend is server-rendered using FastAPI + Jinja2 templates, with vanilla JavaScript handling API calls, file actions, and UI behavior.

## Template Structure

```
app/templates/
├── base.html
├── source.html
├── mapping.html
└── pages/
    ├── dashboard.html
    ├── upload.html
    ├── process.html
    ├── analytics.html
    ├── download.html
    ├── settings.html
    └── index.html
```

`base.html` defines the layout, sidebar, and JS includes. Source-specific pages render via `source.html`.

## Static Assets

```
app/static/
├── css/
│   ├── main.css
│   ├── components.css
│   └── responsive.css
└── js/
    ├── main.js
    ├── components.js
    ├── api.js
    ├── utils.js
    ├── source.js
    └── source_analytics.js
```

## JavaScript Roles

- `api.js`: API wrapper functions
- `source.js`: file upload/preview/processing on source pages
- `source_analytics.js`: analytics page interactions
- `main.js` / `components.js`: layout and UI utilities

## Navigation

The sidebar navigation currently lists:
- Bank of America
- Chase
- Sysco
- Restaurant Depot

GG and AR sources are supported in backend processing but not wired into the default navigation. This is a documented gap for the next phase.

## File Actions UI

The source page supports:
- Uploading files
- Listing input files
- Previewing files
- Triggering processing
- Downloading output files

## Mapping UI

The mapping configuration modal (`mapping.html`) is used to view and update source mapping details, including example data. It depends on `/api/mappings` and `/api/sample-data` endpoints.

## Frontend Constraints

The UI currently assumes CSV-based upload. PDF processing is supported by the backend if PDFs exist on disk, but there is no PDF upload flow in the UI yet.
