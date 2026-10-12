/**
 * Builds the blind rating Google Form (~4 min). Each rater sees only the script they read.
 * Images must already be in your Google Drive, named P01_gpt.png, P01_g25.png, P01_g31.png ... P07_g31.png
 * script.google.com -> New project -> paste -> Save -> Run "buildForm" -> copy the 3 links from the log.
 */
const HINDI = [
  ["P01", "Easy",   "a sweet shop in Varanasi for Diwali",            "शुभ दीपावली"],
  ["P02", "Medium", "a saree shop in Lucknow for the festive season", "त्योहार की ख़ास पेशकश"],
  ["P03", "Hard",   "a mobile repair shop in Patna",                  "मोबाइल रिपेयर – सिर्फ़ ₹199 से शुरू\nसंपर्क करें: 98765 43210"],
];
const BENGALI = [
  ["P05", "Easy",   "a sweet shop in Kolkata for Durga Puja",         "শুভ শারদীয়া"],
  ["P06", "Medium", "a saree shop in Kolkata for Durga Puja",         "পুজোর বিশেষ ছাড়"],
  ["P07", "Hard",   "a restaurant in Siliguri for Durga Puja",        "পুজো স্পেশাল থালি – মাত্র ₹২৪৯"],
];
const MODELS = [["gpt", "OpenAI GPT Image 1"], ["g25", "Google Gemini 2.5 Flash Image"], ["g31", "Google Gemini 3.1 Flash Image Preview"]];
const LABELS = ["Poster A", "Poster B", "Poster C"];
const CONSENT = "I confirm that I am 18 years or older. I voluntarily participated in this evaluation. I consent to my name, email, and responses/ratings being included in this assignment submission for hiring evaluation purposes.";

function imageBlob(file) {
  if (file.getSize() < 2 * 1024 * 1024) return file.getBlob();
  const url = "https://drive.google.com/thumbnail?id=" + file.getId() + "&sz=w1000";
  return UrlFetchApp.fetch(url, { headers: { Authorization: "Bearer " + ScriptApp.getOAuthToken() } }).getBlob();
}
function findImage(name) {
  const it = DriveApp.getFilesByName(name);
  if (!it.hasNext()) throw new Error("Image not found in Drive: " + name);
  return it.next();
}

function addSet(form, ks, lang, n, total, [pid, tier, biz, text]) {
  const page = form.addPageBreakItem()
    .setTitle(lang + " poster set " + n + " of " + total)
    .setHelpText("The AI was asked to make a poster for " + biz + ".\n\nIt had to show EXACTLY this text:\n" + text);
  MODELS.slice().sort(() => Math.random() - 0.5).forEach(([tag, name], j) => {
    const f = findImage(pid + "_" + tag + ".png");
    form.addImageItem().setTitle(LABELS[j]).setImage(imageBlob(f));
    ks.appendRow([pid, lang, tier, LABELS[j], name, f.getName()]);
  });
  form.addGridItem().setTitle("Is the text on each poster correct? (compare with the text above)")
    .setRows(LABELS).setColumns(["Exactly correct", "Small mistakes", "Wrong / unreadable"]).setRequired(true);
  form.addGridItem().setTitle("If this were your shop, would you post it as-is on WhatsApp/Instagram?")
    .setRows(LABELS).setColumns(["Yes", "No"]).setRequired(true);
  form.addMultipleChoiceItem().setTitle("Which poster is best overall?")
    .setChoiceValues(LABELS).setRequired(true);
  return page;
}

function buildForm() {
  const form = FormApp.create("Rate AI Shop Posters – Hindi / Bengali (4 min)");
  form.setDescription(
    "AI image models were asked to make festive shop posters with exact Hindi or Bengali text. " +
    "For each request you'll see 3 posters (A, B, C) from different AI models. Model names are hidden and the order is shuffled. " +
    "Just answer honestly. There are no right answers. Takes about 4 minutes.");
  form.setCollectEmail(true);
  form.setProgressBar(true);

  // Page 1
  form.addTextItem().setTitle("Full name").setRequired(true);
  form.addTextItem().setTitle("Age").setRequired(true)
    .setValidation(FormApp.createTextValidation().setHelpText("You must be 18 or older.").requireNumberGreaterThanOrEqualTo(18).build());
  form.addCheckboxItem().setTitle("Consent").setChoiceValues([CONSENT]).setRequired(true);
  form.addMultipleChoiceItem().setTitle("Do you own or help run a shop or small business?")
    .setChoiceValues(["Yes", "No"]).setRequired(true);
  const langQ = form.addMultipleChoiceItem().setTitle("Which language can you read? (You will only rate posters in that language)").setRequired(true);

  const key = SpreadsheetApp.create("Poster eval – Answer key (keep private)");
  const ks = key.getActiveSheet();
  ks.appendRow(["prompt_id", "language", "difficulty", "label", "company_model", "file"]);

  // Hindi sets
  const hPages = HINDI.map((p, i) => addSet(form, ks, "Hindi", i + 1, HINDI.length, p));
  // Bridge page: Hindi raters who also read Bengali
  const bridge = form.addPageBreakItem().setTitle("Thank you! One last question");
  const moreQ = form.addMultipleChoiceItem().setTitle("Can you also read Bengali and rate 3 Bengali posters? (optional, 2 min)").setRequired(true);
  // Bengali sets
  const bPages = BENGALI.map((p, i) => addSet(form, ks, "Bengali", i + 1, BENGALI.length, p));

  langQ.setChoices([
    langQ.createChoice("Hindi", hPages[0]),
    langQ.createChoice("Bengali", bPages[0]),
    langQ.createChoice("Both Hindi and Bengali", hPages[0]),
  ]);
  moreQ.setChoices([
    moreQ.createChoice("Yes, show me the Bengali posters", bPages[0]),
    moreQ.createChoice("No, submit my answers", FormApp.PageNavigationType.SUBMIT),
  ]);

  Logger.log("FORM (send this link): " + form.getPublishedUrl());
  Logger.log("EDIT form: " + form.getEditUrl());
  Logger.log("ANSWER KEY sheet: " + key.getUrl());
}
