# Vinted Relisting Assistant

A local Windows desktop productivity application for organizing Vinted listings
and preparing a small daily relisting queue.

## Purpose

Vinted Relisting Assistant helps manage listing information locally and suggests
eligible older listings for manual republication.

The application does not automate actions on Vinted.

The user remains responsible for:

- opening Vinted
- uploading photographs
- entering listing information
- publishing listings
- confirming successful relisting inside the assistant

## Safety and Privacy

The application will not:

- scrape Vinted
- use private Vinted APIs
- store Vinted passwords
- access browser cookies
- bypass CAPTCHA or anti-bot systems
- automate publishing or deleting listings
- send listing data to external services

Listing information, photographs, settings, history, and backups remain local.

## Technology

- Python 3.12+
- PySide6
- SQLite
- SQLAlchemy
- Pillow
- pytest

## Development

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1