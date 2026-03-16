# 🎙 Cod Hufan

**cod hufan** waa platform **AI-powered voice enhancement** oo si buuxda u shaqeeya (automated) kuna dhisan **Django**. Waxaad ku **upload** gareyn kartaa video ama audio file kasta, kadibna system-ku wuxuu soo saaraa **studio-quality speech output** oo la **la sifeeyey, la qurxiyey, lana master gareeyey**, iyadoo **speaker-ka codkiisa asalka ah (voice identity)** la ilaalinayo.

## 🎬 Demo

▶️ **Watch the Demo Video**

https://youtu.be/K97AVLtlwr0

---

## ✦ Waxa uu Sameeyo (What It Does)

| Stage       | Technology                | Purpose                                                              |
| ----------- | ------------------------- | -------------------------------------------------------------------- |
| 1 — Extract | **FFmpeg**                | Audio-ga ayaa laga saaraa video-ga kadibna waxaa loo badalaa **WAV** |
| 2 — Isolate | **Demucs (htdemucs_ft)**  | Codka hadalka (speech) ayaa laga soocaa music iyo ambient sound      |
| 3 — Denoise | **DeepFilterNet**         | Waxaa laga saaraa hiss, hum, iyo room noise                          |
| 4 — Enhance | **VoiceFixer**            | sifeynta codka ayaa la hagaajiyaa iyo frequency response           |
| 5 — Master  | **pyloudnorm (EBU R128)** | Loudness normalization, compression, iyo limiting                    |

Output-ka ugu dambeeya wuxuu u dhawaaqayaa sidii lagu duubay **professional studio** oo leh **high-end condenser microphone**, adigoon bedelin qofka codkiisa.

---

# 📋 Requirements

## Python

* **Python 3.10 ama 3.11** ayaa lagula talinayaa

## System

* **FFmpeg** waa inuu ku jiraa system PATH
* **4 GB RAM minimum** (8 GB ama ka badan ayaa fiican files dhaadheer)
* **GPU optional** — stages-ku waxay leeyihiin **CPU fallback**, laakiin **GPU (CUDA)** waxay si weyn u dedejisaa **Demucs** iyo **VoiceFixer**

---

# 🚀 Installation

## Step 1 — Install FFmpeg

### macOS (Homebrew)

```bash
brew install ffmpeg
```

### Ubuntu / Debian

```bash
sudo apt update && sudo apt install -y ffmpeg
```

### Windows

1. Download ka samee
   [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

2. Extract garee kadibna ku dar **bin/** folder-ka **system PATH**

3. Hubi:

```bash
ffmpeg -version
```

---

# Step 2 — Clone / Extract Project-ka

```bash
# Haddii aad isticmaalayso git
git clone <https://github.com/Ruushy/CodHufan-Voice-Studio-AI.git > cod_hufan
cd cod_hufan

# Ama haddii zip la soo dejiyey
cd voice_studio_ai
```

---

# Step 3 — Create Virtual Environment

```bash
python -m venv venv
```

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

---

# Step 4 — Install PyTorch

Ku rakib **PyTorch** ka hor intaadan rakibin requirements kale.

### CPU Only

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### CUDA 12.1 (NVIDIA GPU)

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### CUDA 11.8

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Apple Silicon (MPS)

```bash
pip install torch torchaudio
```

---

# Step 5 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note:** Marka ugu horeysa ee system-ka la kiciyo waxaa si automatic ah loo download gareyn doonaa **AI model weights (~2–4 GB)** oo loogu talagalay:

* Demucs
* VoiceFixer
* DeepFilterNet

Waxaana lagu **cache gareyn doonaa** isticmaalka mustaqbalka.

---

# Step 6 — Setup Django

```bash
python manage.py migrate
python manage.py createsuperuser
```

`createsuperuser` waa ikhtiyaar haddii aad rabto **admin panel**.

---

# Step 7 — Run Server

```bash
python manage.py runserver
```

Browser-ka ka fur:

```
http://127.0.0.1:8000
```

---

# 🎛 Usage

1. Fur **[http://127.0.0.1:8000](http://127.0.0.1:8000)**
2. **Upload** video ama audio file

Supported files:

* `.mp4`
* `.mov`
* `.mkv`
* `.wav`
* `.mp3`
* `.flac`
* iyo kuwo kale

3. Pipeline-ku wuxuu si **automatic ah** uga shaqeynayaa background
4. Marka uu dhamaado waxaad:

* **isbarbardhigi kartaa** codka asalka ah vs kan la hagaajiyey
* **Download** waad dagsan kartaa **studio-quality WAV**

5. Dhamaan jobs-ka waxaa lagu kaydiyaa **History**

```
/jobs/
```

---

# 📁 Project Structure

```
voice_studio_ai/
│
├── manage.py
├── requirements.txt
├── README.md
├── voice_studio.log
│
├── voice_studio_ai/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── voice_app/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── templates/
│
├── audio_pipeline/
│   ├── pipeline_controller.py
│   ├── audio_extractor.py
│   ├── voice_separator.py
│   ├── noise_reduction.py
│   ├── voice_enhancer.py
│   └── audio_mastering.py
│
├── utils/
│   └── file_validator.py
│
└── media/
    ├── uploads/
    └── processed/
```

---

# ⚙ Configuration

Waxaad wax ka beddeli kartaa **voice_studio_ai/settings.py**

| Setting                     | Default     | Description                        |
| --------------------------- | ----------- | ---------------------------------- |
| FILE_UPLOAD_MAX_MEMORY_SIZE | 500 MB      | Maximum upload size                |
| DEBUG                       | True        | Production waa in laga dhigo False |
| SECRET_KEY                  | placeholder | Production waa in la beddelaa      |

---

# 🤖 AI Model Details

## Stage 2 — Voice Isolation

**Demucs (htdemucs_ft)**

* Model ay sameysay **Facebook Research**
* Waxaa si gaar ah loogu fine-tune gareeyey **vocal separation**
* Haddii uusan shaqayn fallback wuxuu noqonayaa **librosa HPSS**

---

## Stage 3 — Noise Reduction

**DeepFilterNet2**

* Real-time deep learning noise suppressor
* Waxaa lagu tababaray kumanaan noise types
* Fallback:

1. `noisereduce`
2. scipy filters

---

## Stage 4 — Voice Enhancement

**VoiceFixer**

Mode 0:

* Voice restoration
* Intelligibility improvement
* Speaker identity lama beddelo

Fallback:

1. **Resemble Enhance**
2. **Parametric EQ**

---

## Stage 5 — Mastering

**pyloudnorm + EBU R128**

* Broadcast standard loudness measurement
* Target:

```
-14 LUFS
```

(YouTube / Podcast standard)

Waxaa lagu daraa:

* Compression (3:1 ratio)
* True peak limiting **-1 dBFS**

---

# 🛠 Troubleshooting

## "FFmpeg not found"

Hubi in **FFmpeg** ku jiro PATH

```bash
ffmpeg -version
```

---

## "CUDA out of memory"

GPU VRAM-ka ayaa laga yaabaa inuu yaraado.

Pipeline-ku wuxuu si automatic ah ugu noqon doonaa **CPU mode**.

Ama waxaad ku qasbi kartaa CPU:

```python
FORCE_CPU = True
```

---

## Models first run download

Marka ugu horeysa:

* Demucs
* VoiceFixer
* DeepFilterNet

waxay download gareynayaan model weights.

Internet connection ayaa loo baahan yahay.

---

## Processing waa gaabis

GPU wuxuu ka dhigi karaa **5–10x faster**

CPU-ga:

* 5 minute video → 10 ilaa 20 minute processing

---

## Port already in use

```bash
python manage.py runserver 8080
```

Kadib fur:

```
http://127.0.0.1:8080
```

---

# 📝 Notes

* Uploaded files → `media/uploads/`
* Processed files → `media/processed/`
* Intermediate files waa la **clean gareeyaa automatic**
* System-ku wuxuu taageeraa **multiple uploads**
* Logs waxaa lagu qorayaa:

```
voice_studio.log
```

---

# 🔒 Production Deployment

Production-ka:

1. `DEBUG = False`
2. Samee **new SECRET_KEY**
3. Configure **ALLOWED_HOSTS**
4. Isticmaal **Gunicorn + Nginx**
5. Isticmaal **Celery + Redis** si background jobs loo maareeyo
6. File storage u isticmaal **S3 ama cloud storage** `MEDIA_ROOT`

