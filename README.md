# argus
you should curate that stuff bro

## Photo processing pipeline

Use `scripts/process-photo.py` to build `src/data/photos.json` from images in `src/photos`.
If you want AI-generated review text during the build, provide the API connection details:

```
PHOTO_REVIEW_API_URL=https://your-reviewer.example.com/review \
PHOTO_REVIEW_API_KEY=secret-token \
python scripts/process-photo.py
```

The script will upload each new photo to the review API, attach the returned `summary`,
`strengths`, `critique`, and `actions` fields under `analysis.aiReview`, and persist the
results back to the dataset. Review calls are skipped if `PHOTO_REVIEW_API_URL` is unset.
