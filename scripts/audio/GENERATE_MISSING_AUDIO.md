# Generate Missing Audio Files (119 Pinyins)

## Background

When we enhanced `chinese_characters.csv` with pypinyin heteronyms (`build_step6_enrich_pypinyin.py`), we added 119 new rare pinyin variants that don't have audio files yet.

Most of these are neutral tone (tone 0) grammatical particles like:
- `jie0` (假 particle usage)
- `he0` (和 particle usage)
- `de0` (的/地/得 particles)

## Steps to Generate Missing Audio

### 1. Verify Updated Syllables File

✅ Already done! The syllables_enumeration.json has been updated with 119 new entries:
- **Old**: 1,478 syllables
- **New**: 1,597 syllables (+ 119 missing)

### 2. Run Audio Generation Script

The existing `generate_audio_aws.py` script has resume functionality built-in. It will:
- Skip existing audio files (1,478 already exist)
- Generate only the 119 missing files
- Save to `data/audio/syllables/`

```bash
cd /Users/brianliou/projects/hanzi-flow

# Make sure boto3 is installed
pip install boto3

# Configure AWS credentials if not already done
# aws configure

# Run the generation (it will show what it's going to generate)
python scripts/audio/generate_audio_aws.py
```

### 3. Expected Outcome

The script will:
- Detect 1,478 existing .ogg files
- Generate 119 new .ogg files
- Estimated time: ~18 minutes (119 × 0.15s rate limit)
- Estimated cost: ~$0.0002 USD (well within free tier)

### 4. Move Files to Production

After generation completes:

```bash
# Copy the 119 new files from syllables/ to production audio folder
cp data/audio/syllables/*.ogg app/public/data/audio/

# Verify count
ls app/public/data/audio/*.ogg | wc -l
# Should show: 1597 files
```

## Missing Pinyins List (119 total)

For reference, here are all the missing pinyins being generated:

```
bing0, cai0, che0, chen0, cheng0, chou0, chun0, cou3, cun0, dan0, dang0,
dao0, dei1, du0, ei3, ei4, fan0, fen0, gai0, gu0, guo0, ha4, hang3, hao0,
he0, hen1, hng0, hou0, hua0, huai0, huan0, huang0, ji0, jiang0, jie0, ke0,
kou0, kuai0, len4, li0, lie0, ling1, long0, long1, lou0, luo0, m0, mai0,
mao0, mei0, mian0, mie0, mou0, mu0, na0, na1, nai0, nan0, nang0, nao0, ne2,
ng0, niang0, niu0, nun4, o3, o4, ou0, pan0, peng0, ping3, pou4, qin0, que0,
r0, ran0, re2, ren0, rong1, sao0, shao0, shen0, shou2, shu0, shuo2, sou0,
su0, suan0, sun4, tan0, tang0, tei1, teng0, ti0, tian0, ting0, tong0, tuo0,
wang0, xi0, xia0, xie0, xiong0, xun0, ying0, yo0, yong0, yuan0, yue0, yue2,
za4, zan0, zha0, zhan0, zhan2, zhei4, zheng0, zhou0, zhui0
```

## Troubleshooting

**Issue**: Audio files already exist but pinyin still fails
- **Solution**: Check that file naming matches exactly (e.g., `jie0.ogg` not `Jie0.ogg`)

**Issue**: AWS credentials error
- **Solution**: Run `aws configure` and enter your AWS access key + secret

**Issue**: Some pinyins fail to generate
- **Solution**: Check generation_results.json for error details. Some pinyins (like `hng0`, `ng0`, `m0`) might be unsupported by AWS Polly.

## Next Steps After Generation

1. Test a few audio files to ensure quality
2. Update the app to handle missing audio gracefully (already done - playPinyinAudio shows warnings)
3. Consider fallback behavior for truly unsupported pinyins (like `m0`, `ng0`)
