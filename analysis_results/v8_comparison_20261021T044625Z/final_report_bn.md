# V8 Profile Comparison — প্রাথমিক রিপোর্ট

- প্রকল্প: `/data/data/com.termux/files/home/dcim_calibration`
- আউটপুট: `/data/data/com.termux/files/home/dcim_calibration/analysis_results/v8_comparison_20261021T044625Z`
- সময় UTC: `2026-10-21T04:46:42.832570+00:00`
- সিদ্ধান্ত: **INCONCLUSIVE**

## যাচাইকৃত সীমা
- XML difference rows: 2644
- JPEG metric rows: 6
- Decode PASS: 6

## সতর্কতা
- XML parse PASS হলে শুধু XML গঠন বৈধ বোঝায়; LMC-তে runtime প্রয়োগ প্রমাণ হয় না।
- ভিন্ন framing বা exposure-এর JPEG-কে controlled matched pair ধরা হয়নি।
- JPEG luma/saturation হলো বর্ণনামূলক মেট্রিক; dynamic range, color accuracy বা sensor noise নয়।
- বর্তমান runtime verification এই স্ক্রিপ্ট থেকে সম্ভব হয়নি।

## পরবর্তী পদক্ষেপ
1. `capture_protocol_bn.md` অনুসারে নিয়ন্ত্রিত capture নিন।
2. `capture_manifest_template.csv` পূরণ করুন; অজানা মান ফাঁকা রাখুন।
3. সব capture একই project-এর অধীনে রাখুন এবং পরবর্তী অডিটে সেগুলো দিন।
