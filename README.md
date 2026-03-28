# NSKAILabs Backend

Open-source research community platform backend for nanophotonics and metasurfaces.

## Tech Stack

- **Framework:** Django 5.x + Django REST Framework
- **Database:** PostgreSQL (Neon serverless)
- **Authentication:** Magic Link (passwordless email)
- **Deployment:** Railway

## Quick Start

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/your-org/nskailabs-backend.git
cd nskailabs-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your values
nano .env
```

Required variables:
- `SECRET_KEY` - Django secret key
- `DATABASE_URL` - Neon PostgreSQL connection string
- `EMAIL_HOST_USER` & `EMAIL_HOST_PASSWORD` - For sending magic links
- `FRONTEND_URL` - Your frontend URL (for magic link redirects)

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
python manage.py runserver
```

Visit http://localhost:8000/api/health/ to verify.

---

## API Documentation

### Authentication (Magic Link)

#### Request Magic Link
```http
POST /api/auth/request-magic-link/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Magic link sent to your email.",
  "email": "user@example.com",
  "expires_in_minutes": 15
}
```

#### Verify Magic Link
```http
POST /api/auth/verify-magic-link/
Content-Type: application/json

{
  "token": "uuid-token-from-email-link"
}
```

**Response:**
```json
{
  "message": "Authentication successful.",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "user",
    "full_name": "User Name",
    "profile": {
      "bio": null,
      "institution": null,
      "research_interests": []
    }
  },
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  },
  "is_new_user": false
}
```

#### Refresh Token
```http
POST /api/auth/refresh/
Content-Type: application/json

{
  "refresh": "refresh-token"
}
```

#### Get Current User
```http
GET /api/auth/user/
Authorization: Bearer <access-token>
```

#### Update Profile
```http
PUT /api/auth/profile/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "bio": "Researcher in nanophotonics",
  "institution": "MIT",
  "research_interests": ["metasurfaces", "photonics"],
  "google_scholar": "https://scholar.google.com/...",
  "orcid": "0000-0001-2345-6789"
}
```

#### Logout
```http
POST /api/auth/logout/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "refresh": "refresh-token"
}
```

---

### Research Papers

#### List Papers
```http
GET /api/research/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category: `fundamentals`, `tutorial`, `research`, `news`, `review` |
| `tag` | string | Filter by tag |
| `search` | string | Search in title, abstract, content |
| `featured` | boolean | Only featured papers |
| `author` | integer | Filter by author ID |
| `ordering` | string | Sort: `published_at`, `-published_at`, `views`, `-views` |
| `page` | integer | Page number |
| `page_size` | integer | Items per page (max 50) |

**Response:**
```json
{
  "count": 42,
  "next": "http://api/research/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Introduction to Metasurfaces",
      "slug": "introduction-to-metasurfaces",
      "subtitle": "A comprehensive guide",
      "abstract": "...",
      "category": "fundamentals",
      "tags": ["metasurfaces", "optics"],
      "author": {
        "id": 1,
        "username": "researcher",
        "full_name": "Dr. Jane Smith",
        "avatar_url": "...",
        "institution": "MIT"
      },
      "featured_image": "https://...",
      "is_featured": true,
      "views": 1234,
      "reading_time": 12,
      "like_count": 56,
      "comment_count": 8,
      "published_at": "2026-01-15T10:30:00Z"
    }
  ]
}
```

#### Get Paper Detail
```http
GET /api/research/{slug}/
```

#### Toggle Like (Authenticated)
```http
POST /api/research/{id}/like/
Authorization: Bearer <access-token>
```

**Response:**
```json
{
  "liked": true,
  "like_count": 57
}
```

#### Add Comment (Authenticated)
```http
POST /api/research/{id}/add_comment/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "content": "Great paper! Very helpful.",
  "parent": null
}
```

#### Get Comments
```http
GET /api/research/{id}/comments/
```

---

### Categories & Tags

#### List Categories
```http
GET /api/categories/
```

**Response:**
```json
[
  {"id": "fundamentals", "name": "Fundamentals", "count": 15},
  {"id": "tutorial", "name": "Tutorial", "count": 8},
  {"id": "research", "name": "Research", "count": 25},
  {"id": "news", "name": "News", "count": 10},
  {"id": "review", "name": "Review", "count": 5}
]
```

#### List Tags
```http
GET /api/tags/
```

**Response:**
```json
[
  {"name": "metasurfaces", "count": 20},
  {"name": "photonics", "count": 15},
  {"name": "simulation", "count": 12}
]
```

---

### Featured Content (Homepage)

```http
GET /api/featured/
```

**Response:**
```json
{
  "featured_papers": [...],
  "recent_papers": [...],
  "announcements": [...],
  "featured_tools": [...]
}
```

---

### Tools

#### List Tools
```http
GET /api/tools/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `tag` | string | Filter by tag |
| `featured` | boolean | Only featured tools |
| `search` | string | Search in name, description |

#### Get Tool Detail
```http
GET /api/tools/{slug}/
```

---

### Newsletter

#### Subscribe
```http
POST /api/newsletter/subscribe/
Content-Type: application/json

{
  "email": "subscriber@example.com",
  "name": "John Doe",
  "interests": ["metasurfaces", "tutorials"]
}
```

#### Unsubscribe
```http
POST /api/newsletter/unsubscribe/
Content-Type: application/json

{
  "email": "subscriber@example.com"
}
```

---

### Contact

```http
POST /api/contact/
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "organization": "University",
  "message": "I'd like to collaborate..."
}
```

---

### Announcements

```http
GET /api/announcements/
```

---

## Deployment (Railway)

### 1. Connect Repository

Connect your GitHub repository to Railway.

### 2. Set Environment Variables

In Railway dashboard, add all variables from `.env.example`.

### 3. Deploy

Railway will automatically:
- Build using `Dockerfile`
- Run migrations
- Start gunicorn server

### 4. Custom Domain

Add your custom domain in Railway settings:
- `api.nskailabs.com`

---

## Database Models

```
UserProfile
├── user (OneToOne → User)
├── bio, institution, department
├── research_interests (JSON)
├── website, google_scholar, orcid
├── twitter, linkedin, avatar_url
└── is_contributor

MagicLink
├── email
├── token (UUID, unique)
├── expires_at (15 minutes)
└── is_used

ResearchPaper
├── title, slug, subtitle, abstract, content
├── category, tags (JSON)
├── author, co_authors (M2M)
├── featured_image, pdf_url, github_url, doi
├── original_paper_* (reference fields)
├── status, is_featured, views, reading_time
└── published_at

Comment
├── paper, author, content
├── parent (self-reference for nesting)
└── is_approved

Like
├── paper, user
└── unique_together

Tool
├── name, slug, description
├── github_url, demo_url, documentation_url
├── author, tags, stars
└── is_featured

NewsletterSubscriber
├── email (unique), name
├── interests (JSON)
└── is_active
```

---

## License

MIT License - See LICENSE file.

## Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request

## Support

- Email: admin@nskailabs.com
- Issues: GitHub Issues
