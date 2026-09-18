# Vinted Relisting Assistant Import Format

The application can import listings from local JSON and CSV files.

No Vinted account connection, scraping, browser cookies, or external API is used.

## Minimum required data

Every listing needs:

- title
- price

Everything else is optional.

---

## JSON format

A file can contain one listing:

```json
{
  "title": "Vintage black handbag",
  "description": "Black handbag in very good condition.",
  "price": 12.00,
  "currency": "EUR",
  "brand": "Unknown",
  "condition": "Very good"
}
```

Or multiple listings:

```json
[
  {
    "title": "Vintage black handbag",
    "description": "Black handbag in very good condition.",
    "price": 12.00,
    "currency": "EUR",
    "category": "Women > Bags",
    "brand": "Unknown",
    "condition": "Very good",
    "colour": "Black",
    "material": "Faux leather",
    "original_created_date": "2026-01-12",
    "priority": "Normal"
  },
  {
    "title": "Knitted cardigan",
    "description": "Soft cardigan.",
    "price": 8.00,
    "currency": "EUR",
    "size": "M",
    "condition": "Good",
    "original_created_date": "2026-02-01"
  }
]
```

---

## Supported fields

```text
title
description
price
currency
category
subcategory
brand
size
condition
colour
color
material
parcel_size
notes
original_created_date
last_relisted_date
number_of_times_relisted
relist_count
priority
status
sold
archived
manually_excluded
paused_until
paused_indefinitely
photos
```

`color` is accepted as an alias for `colour`.

`relist_count` is accepted as an alias for `number_of_times_relisted`.

---

## Dates

Recommended format:

```text
YYYY-MM-DD
```

Example:

```text
2026-09-01
```

These formats are also accepted:

```text
DD/MM/YYYY
DD-MM-YYYY
DD.MM.YYYY
```

---

## Priority

Allowed values:

```text
High
Normal
Low
```

---

## Status

Allowed values:

```text
Active
Paused
Sold
Archived
```

---

## Boolean fields

For fields such as `sold` and `archived`, the importer accepts:

```text
true
false
yes
no
1
0
```

---

## CSV format

The first row must contain column names.

Example:

```csv
title,description,price,currency,brand,size,condition,colour,original_created_date,priority
Vintage black handbag,Black handbag in very good condition,12.00,EUR,Unknown,,Very good,Black,2026-01-12,Normal
Knitted cardigan,Soft knitted cardigan,8.00,EUR,Unknown,M,Good,Blue,2026-02-01,Normal
```

You do not need to include every supported column.

---

## Photos

JSON may contain a photos field:

```json
{
  "title": "Vintage black handbag",
  "price": 12.00,
  "photos": [
    "C:/Users/User/Downloads/bag1.jpg",
    "C:/Users/User/Downloads/bag2.jpg"
  ]
}
```

Stage 5.5 detects that photo information exists but intentionally does not save those paths.

Stage 6 will copy those images into the application's own storage, for example:

```text
data/listings/123/photos/
```

This ensures listings do not break if the original files are later deleted from Downloads, Desktop, or another folder.

---

## Duplicate imports

The importer does not currently guess whether two similar listings are duplicates.

Importing the same CSV or JSON file twice can therefore create duplicate records.

This is intentional because two legitimate listings can have the same title and price.