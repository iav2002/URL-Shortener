# Serverless URL Shortener

A lightweight, serverless URL shortener API built with Python and Flask. This project leverages Supabase for database storage and authentication, and is designed to be deployed on Vercel.

currently down for renovations

![image]diagram.svg)


## Tech Stack

* **Language:** Python 3.9+
* **Framework:** Flask
* **Database & Auth:** Supabase (PostgreSQL)
* **Deployment:** Vercel (Serverless Functions)

## Features

* **Shorten URLs:** Generates unique short codes for long URLs.
* **Authentication:** Restricted link creation using Supabase Auth (JWT).
* **Redirection:** High-performance redirection with click tracking.
* **Stateless:** Designed for serverless environments (Vercel).

## Prerequisites

* Python 3.9 or higher
* A Supabase account and project
* Vercel CLI (for deployment)
