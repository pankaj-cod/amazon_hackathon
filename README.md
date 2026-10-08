# Parali Mitra (ਪਰਾਲੀ ਮਿੱਤਰ · पराली मित्र)

A stubble-burning check-up for Punjab and Haryana farmers. Drop a pin on your field, or draw its
boundary, and in about a minute you get:

- **Burn history** for the last 7 paddy seasons, read from 10 m Sentinel-2 satellite images.
- **What burning cost you:** the fertiliser (N, P, K) value lost per burn and in total, the soil
  organic carbon you gave up, and the PM2.5 smoke released.
- **Carbon-credit income** you could earn by stopping, shown as a ₹ range per acre with every
  assumption listed.
- **Advice in Punjabi, Hindi or English**, written by Claude on Amazon Bedrock.

Built for the AWS student hackathon (Air track). It extends our earlier
[Carbon-Offset-Analyser](https://github.com/pankaj-cod/Carbon-Offset-Analyser): the first commit
here is that code unchanged.

## How it works

```
phone browser ──► Next.js static site (AWS Amplify)
                     │  POST /compute/direct {pin|polygon, acres, language}
                     ▼
              AWS Lambda (FastAPI container, us-west-2) ── S3 cache
                     │
     ┌───────────────┼──────────────────────┐
     ▼               ▼                      ▼
Sentinel-2 L2A   ISRIC SoilGrids     Amazon Bedrock
(AWS Open Data)  (soil carbon)       (Claude: advice)
```

1. **Burn detection** (`apps/api/app/services/stubble/burn.py`): for each October–November we read
   every clear Sentinel-2 scene over the field. A pixel counts as burned when it turns dark char
   (low red and NIR, SWIR2 above NIR, NBR < −0.08) within 20 days of being green paddy or
   stubble. Active flames, where SWIR2 saturates, also count. Thresholds were calibrated by eye
   against burn scars near Sangrur in 2023. Tilled or irrigated soil after sowing is rejected
   because it stays brighter in red. Seasons with too few clear images are reported as *unclear*,
   not as *not burned*.
2. **Impact** (`economics.py`):
   - Straw is 5.5–7.5 t/ha, of which 80% burns (IPCC 2006).
   - Methane and nitrous oxide are converted with IPCC AR6 GWPs. Biogenic CO₂ is reported but
     never credited.
   - Nutrient losses use the ICAR/PAU per-tonne figures, priced at subsidised fertiliser rates.
   - Retaining residue adds 0.15–0.5 t C/ha/yr of soil carbon.
3. **Carbon credits**: avoided non-CO₂ emissions (counted only if the field burned in the last
   3 seasons) plus soil carbon, minus a 20–40% uncertainty and buffer deduction. Credits are
   valued at US$5–15 per tonne, and the farmer keeps 50–70% after the aggregator's cut.
   Typical result: ₹50–700 per acre per year. The fertiliser saved is worth far more, and the
   app says so.

## AWS services

| Service | Role |
|---|---|
| **AWS Open Data (Sentinel-2 COGs on S3)** | Satellite imagery, read directly from `s3://sentinel-cogs` with no credentials |
| **AWS Lambda + Function URL** | API (container image, arm64, in us-west-2 next to the data) |
| **Amazon S3** | Cache of per-field analyses |
| **Amazon Bedrock** | Claude writes the advice in Punjabi, Hindi or English from the computed facts |
| **AWS Amplify Hosting** | Static Next.js site |

## Run locally

Requires Python 3.12 and Node 18+. AWS credentials are optional: without them the advice comes
from built-in Punjabi, Hindi and English text.

```bash
npm run setup
```

```bash
npm run dev
```

Then open http://localhost:3000 and tap **Try a sample field**. That field's satellite results
are pre-computed in `apps/api/demo_cache/`, so it returns instantly. A new field takes 30–60 s
from India and a few seconds when the API runs on AWS in us-west-2.

```bash
npm run test:api
```

## Deploy to AWS

You need an AWS account (an AWS Builder ID alone cannot create resources), the AWS CLI, the SAM
CLI and Docker.

1. In the Bedrock console (us-west-2), check model access for Claude. If `anthropic.claude-opus-5-5`
   is not enabled for your account, deploy with
   `--parameter-overrides BedrockModelId=anthropic.claude-sonnet-5`, which is open to all
   Bedrock customers.
2. Deploy the API:

   ```bash
   cd infrastructure/aws && sam build && sam deploy --guided --region us-west-2
   ```

   Copy the `ApiUrl` output.
3. Host the web app on Amplify: connect this GitHub repo, set the app root to `apps/web`, the
   build command to `npm run build`, the output directory to `out`, and the environment variable
   `NEXT_PUBLIC_BACKEND_URL` to the `ApiUrl`. Then redeploy the API with
   `AllowedOrigin=https://<your-amplify-domain>`.
4. Check it:

   ```bash
   curl <ApiUrl>health
   ```

   If this returns 403, grant public invoke:
   `aws lambda add-permission --function-name <fn> --statement-id url-invoke --action lambda:InvokeFunction --principal "*" --invoked-via-function-url`.

## Limits and honesty

- These are estimates. Detection is tuned to avoid false "burned" verdicts, so a burn followed by
  tillage within a cloudy gap can be missed.
- A pin covers a 50 m square, so draw the boundary for small or narrow fields.
- SoilGrids is coarse (250 m) and tends to over-estimate soil carbon in the Indo-Gangetic plain.
  It is used only to put losses in context.
- Carbon-credit income requires joining an aggregated project (e.g. Verra VM0042). Small fields
  cannot sell credits alone.

## Repository layout

```
apps/api/app/services/stubble/   burn detection, satellite I/O, soil, economics, advice
apps/api/app/routers/compute.py  POST /compute/direct
apps/web/                        Next.js mobile app (static export)
infrastructure/aws/template.yaml SAM template (Lambda, Function URL, S3, IAM)
apps/api/scripts, apps/api/ml    legacy Carbon-Offset-Analyser tools (unchanged; requirements-ml.txt)
```
