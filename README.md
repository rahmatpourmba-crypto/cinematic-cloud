# تولید خودکار ویدیوهای سینمایی با گوگل‌کلود + گیت‌هاب اکشن

پایپلاین کامل تولید ویدیوی سینمایی «قصه‌های قرآنی» با:

- **Remotion (React)** — مونتاژ ویدیو ۴K/۱۰۸۰p با Ken Burns، دانه فیلم، وینیت، لوتموتو، برش سینمایی و تایپوگرافی طلایی
- **Vertex AI Imagen** — تولید تصاویر فوتورئال سینمایی (با fallback خودکار به Pollinations.ai برای حالت رایگان)
- **Google Cloud Text-to-Speech** — صدای راوی فارسی (با fallback به edge-tts)
- **Cloud Run** — سرویس ابری همیشه‌در دسترس
- **GitHub Actions** — دیپلوی خودکار + اجرای زمان‌بندی‌شده (cron)

## ساختار

```
cinematic-cloud/
├── src/                  # کامپوزیشن‌های Remotion (CinematicStory, StoryThumbnail)
├── public/scenes|audio   # خروجی assetها (صدا و تصویر تولیدشده)
├── server/               # FastAPI + پایپلاین پایتون (Imagen, TTS, render, YouTube)
├── scripts/local_render.py
├── app.json              # دیتابیس داستان‌ها (عنوان، راوی، پرامپت تصویر)
├── Dockerfile            # تصویر Cloud Run (Node+Chrome+Python+ffmpeg)
├── cloudbuild.yaml
└── .github/workflows/
    ├── deploy.yml        # push → ساخت ایمج → دیپلوی روی Cloud Run
    ├── render.yml        # cron هفتگی → فراخوانی سرویس Cloud Run
    └── render-runner.yml # (اختیاری) رندر مستقیم روی runner گیت‌هاب بدون GCP
```

## اجرای محلی

```bash
npm ci
pip install -r requirements.txt
npx remotion browser ensure           # یک‌بار برای دانلود Chrome headless

# ساخت یک داستان (تصاویر Pollinations + صدا edge-tts — رایگان)
python scripts/local_render.py --story solomon_hoopoe --episode 1

# لیست داستان‌ها
python scripts/local_render.py --list
```

خروجی در `out/` ساخته می‌شود.

## راه‌اندازی گوگل‌کلود (یک‌بار)

1. پراجکت بسازید و APIهای زیر را enable کنید:
   ```bash
   gcloud services enable run.googleapis.com artifactregistry.googleapis.com \\
       aiplatform.googleapis.com texttospeech.googleapis.com storage.googleapis.com
   ```
2. سرویس‌اکانت بسازید و سطوح زیر را بدهید (روی SA یا پراجکت):
   - `roles/run.admin`, `roles/artifactregistry.admin`
   - `roles/aiplatform.user` (Imagen)
   - `roles/texttospeech.admin`
   - `roles/storage.objectAdmin`
3. **Workload Identity Federation** برای گیت‌هاب:
   ```bash
   gcloud iam workload-identity-pools create gh-pool --location=global
   gcloud iam workload-identity-pools providers create-oidc gh-provider \
       --location=global --workload-identity-pool=gh-pool \
       --issuer-uri=https://token.actions.githubusercontent.com \
       --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor" \
       --attribute-condition="assertion.repository_owner=='YOUR_GITHUB_USER'"
   WIP=$(gcloud iam workload-identity-pools describe gh-pool --location=global \\
         --format='value(name)')
   gcloud iam service-accounts add-iam-policy-binding SA_EMAIL \
       --role=roles/iam.workloadIdentityUser \
       --member="principalSet://iam.googleapis.com/$WIP/attribute.repository/YOUR_GITHUB_USER/*"
   ```
4. کانتینر رجیستری:
   ```bash
   gcloud artifacts repositories create cinematic-artifacts \\
       --repository-format=docker --location=us-central1
   ```

### سکرت‌ها و وریبل‌های گیت‌هاب

| نوع | نام | توضیح |
|---|---|---|
| Secret | `GCP_WORKLOAD_IDENTITY_PROVIDER` | شناسه provider از مرحله قبل |
| Secret | `GCP_SERVICE_ACCOUNT` | ایمیل SA |
| Variable | `GCP_PROJECT` | نام پراجکت |
| Variable | `GCP_REGION` | مثلاً `us-central1` |
| Variable | `ARTIFACT_REPO` | `cinematic-artifacts` |
| Variable | `GCS_BUCKET` | (اختیاری) برای آپلود خروجی |
| Variable | `CINEMATIC_URL` | URL سرویس Cloud Run بعد از دیپلوی |
| Secret | `YOUTUBE_TOKEN_B64` | (اختیاری) توکن OAuth یوتیوب — base64 فایل `token_*.pickle` |
| Secret | `YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN` | روش جایگزین اتصال یوتیوب |

## دیپلوی

با هر `push` به شاخه `main` ، workflow `deploy.yml` تصویر را می‌سازد و روی Cloud Run دیپلوی می‌کند:

```bash
# یا دستی:
gcloud builds submit --config=cloudbuild.yaml --substitutions=_IMAGE=us-central1-docker.pkg.dev/PROJECT/cinematic-artifacts/cinematic-cloud:manual .
gcloud run deploy cinematic-cloud --image=... --region=us-central1 --no-allow-unauthenticated
```

> نکته: سرویس با IAM محافظت می‌شود (`--no-allow-unauthenticated`)؛ فراخوانی با
> `gcloud auth print-access-token` صورت می‌گیرد.

## زمان‌بندی خودکار

`render.yml` هر چهارشنبه ساعت ۰۵:۰۰ UTC فراخوانی می‌شود (یا دستی از تب Actions):

```bash
# تست سریع:
curl -X POST "$CINEMATIC_URL/render" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{"story_id":"solomon_hoopoe","episode":1,"upload":true}'
```

### نکات هزینه و محدودیت

- Cloud Run حداکثر **۶۰ دقیقه** در هر درخواست — برای ویدیوی ۳ تا ۶ دقیقه‌ای ۱۰۸۰p کافی است.
- رندر ۴K روی CPU کند است؛ برای کیفیت‌های بالا یک VM با GPU یا `--cpu=4` پیشنهاد می‌شود (ریز را با `WIDTH/HEIGHT` تنظیم کنید).
- بدون `GCS_BUCKET` و بدون واریبل‌های Google، پایپلاین با Pollinations + edge-tts **رایگان** اجرا می‌شود.
- `min-instances=0` یعنی بدون ترافیک، هزینه صفر (سرد شروع می‌شود).

## دیباگ

- لاگ‌ها: `gcloud run services logs read cinematic-cloud`
- تست Health: `curl $CINEMATIC_URL/health`
- رندر مشکل‌دار: `python scripts/local_render.py --story X --episode 1` روی رانر گیت‌هاب