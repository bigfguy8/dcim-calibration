# নিয়ন্ত্রিত V8 Capture Protocol

প্রোফাইল A: LXX521_IMX682_V8_ProBalanced.xml
প্রোফাইল B: LXX521_IMX682_V8_FullAllRounder_Q100.xml

## দৃশ্য
1. দিনের আলো ও সূক্ষ্ম ডিটেইল
2. উজ্জ্বল জানালা ও অন্ধকার ঘর
3. গভীর ছায়া ও shadow texture
4. নিরপেক্ষ রং ও বৈধ color reference
5. slanted-edge target ও fine texture
6. কম আলো

## প্রতি দৃশ্যে
- প্রথম পাঁচ দৃশ্যে প্রতি প্রোফাইলে অন্তত ৫টি capture।
- Low-light দৃশ্যে প্রতি প্রোফাইলে অন্তত ১০টি capture।
- স্থির ফোন/ট্রাইপড, একই lens, distance, framing, lighting ও focus রাখুন।
- সম্ভব হলে order ব্যবহার করুন A,B,B,A,A,B,B,A,A,B; অন্য দৃশ্যে B দিয়ে শুরু করুন।
- প্রতি capture-এর timestamp, profile, resolution, exposure, ISO, WB, HDR state,
  camera ID ও SHA-256 লিখুন; অনুপস্থিত মান ফাঁকা রাখুন।
- ব্যর্থ capture ও retake মুছবেন না; কারণ নথিভুক্ত করুন।
- Burst/HDR stacking/temporal denoising থাকলে frames-কে স্বাধীন sample ধরে নেবেন না।
- একই profile বারবার নির্বাচন করার পর LMC UI-তে active selection যাচাই করুন।
- XML setting উপস্থিত থাকা মানেই runtime-এ প্রয়োগ হওয়া নয়।
