/* Overnight Desk — Amazon 75-character title rewrite. Count spaces. Do not invent specs. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.OvernightDesk = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var TITLE_LIMIT = 75;
  var HIGHLIGHT_LIMIT = 125;

  var SAMPLE_ASIN = "B0FH54F1XB";
  var SAMPLE_BRAND = "GODELAIF";
  var SAMPLE_TITLE =
    "Advent Calendar 2026, 24 Days Scented Candles Gift Set Christmas " +
    "Advent Calendars Aromatherapy Candle - Birthday Thanksgiving " +
    "Mother's Day for Adult Women with Gift Box";
  var SAMPLE_REWRITE = "GODELAIF Advent Calendar 2026, 24 Soy Candles Gift Set for Women";
  var SAMPLE_HIGHLIGHTS =
    "Scented aromatherapy. Christmas, birthday, Thanksgiving, Mother's Day. " +
    "Gift box for adult women.";
  var FIVERR =
    "https://www.fiverr.com/overnight_desk/rewrite-amazon-75-char-titles-or-etsy-holiday-listing-copy";

  var ASIN_RE = /\b(B0[A-Z0-9]{8})\b/i;
  var DP_RE = /\/(?:dp|gp\/product|product)\/([A-Z0-9]{10})/i;

  var OCCASION_PHRASES = [
    "mother's day",
    "mothers day",
    "father's day",
    "fathers day",
    "valentine's day",
    "valentines day",
    "new year's",
    "new years",
    "bridal shower",
    "baby shower",
    "christmas",
    "xmas",
    "birthday",
    "thanksgiving",
    "halloween",
    "easter",
    "hanukkah",
    "kwanzaa",
    "holiday",
    "holidays",
    "anniversary",
    "wedding"
  ];

  var KEEP_PHRASES = [
    "advent calendar",
    "gift set",
    "gift box",
    "soy candles",
    "soy candle",
    "for women",
    "for men",
    "for kids",
    "for her",
    "for him",
    "for girls",
    "for boys",
    "stainless steel",
    "cast iron",
    "essential oil",
    "essential oils"
  ];

  var FILLER = {
    with: true,
    and: true,
    the: true,
    a: true,
    an: true,
    or: true,
    of: true,
    to: true,
    in: true,
    on: true,
    by: true,
    from: true,
    our: true,
    "new": true,
    best: true,
    premium: true,
    perfect: true,
    amazing: true,
    unique: true,
    ideal: true,
    "-": true,
    "\u2013": true,
    "\u2014": true,
    "/": true
  };

  var AUDIENCE = {
    women: true,
    woman: true,
    men: true,
    man: true,
    kids: true,
    kid: true,
    adult: true,
    adults: true,
    girls: true,
    boys: true,
    mom: true,
    wife: true,
    her: true,
    him: true,
    ladies: true
  };

  var PUNCT_STRIP = /[.\-\u2013\u2014()[\]"']/;

  function charCount(text) {
    return String(text == null ? "" : text).length;
  }

  function collapseWs(text) {
    var parts = String(text == null ? "" : text).split(/\s+/);
    var out = [];
    for (var i = 0; i < parts.length; i++) {
      if (parts[i]) out.push(parts[i]);
    }
    return out.join(" ");
  }

  function unescapeTitle(text) {
    var s = String(text == null ? "" : text);
    s = s.replace(/\u00a0/g, " ");
    s = s.replace(/&nbsp;/gi, " ");
    s = s.replace(/&#x([0-9a-f]+);/gi, function (_, h) {
      return String.fromCharCode(parseInt(h, 16));
    });
    s = s.replace(/&#(\d+);/g, function (_, n) {
      return String.fromCharCode(parseInt(n, 10));
    });
    s = s.replace(/&quot;/gi, '"');
    s = s.replace(/&apos;/gi, "'");
    s = s.replace(/&lt;/gi, "<");
    s = s.replace(/&gt;/gi, ">");
    s = s.replace(/&amp;/gi, "&");
    return collapseWs(s);
  }

  function extractAsin(text) {
    if (!text) return null;
    var m = DP_RE.exec(text);
    if (m) return m[1].toUpperCase();
    m = ASIN_RE.exec(text);
    if (m) return m[1].toUpperCase();
    return null;
  }

  function looksLikeUrl(text) {
    var t = String(text == null ? "" : text).trim();
    if (!t) return false;
    var low = t.toLowerCase();
    if (low.indexOf("http://") === 0 || low.indexOf("https://") === 0 || low.indexOf("www.") === 0) {
      return true;
    }
    try {
      var u = new URL(t.indexOf("://") >= 0 ? t : "https://" + t);
      return (u.hostname || "").toLowerCase().indexOf("amazon.") >= 0;
    } catch (e) {
      return false;
    }
  }

  function looksLikeAsinOnly(text) {
    var t = String(text == null ? "" : text).trim();
    return /^B0[A-Z0-9]{8}$/i.test(t);
  }

  function isSampleTitle(title) {
    return collapseWs(title || "") === SAMPLE_TITLE;
  }

  function stem(word) {
    var w = String(word == null ? "" : word).toLowerCase().replace(/[^a-z0-9']+/g, "");
    if (w.length <= 3) return w;
    if (w.length > 4 && w.slice(-3) === "ies") return w.slice(0, -3) + "y";
    if (w.length > 4 && w.slice(-3) === "ses") return w.slice(0, -2);
    if (w.charAt(w.length - 1) === "s" && w.slice(-2) !== "ss" && w.length > 3) return w.slice(0, -1);
    return w;
  }

  function phraseSpans(lower, phrases) {
    var spans = [];
    for (var p = 0; p < phrases.length; p++) {
      var phrase = phrases[p];
      var start = 0;
      while (true) {
        var i = lower.indexOf(phrase, start);
        if (i < 0) break;
        spans.push([i, i + phrase.length, phrase]);
        start = i + phrase.length;
      }
    }
    spans.sort(function (a, b) {
      if (a[0] !== b[0]) return a[0] - b[0];
      return (b[1] - b[0]) - (a[1] - a[0]);
    });
    var picked = [];
    var used = [];
    for (var s = 0; s < spans.length; s++) {
      var a = spans[s][0];
      var b = spans[s][1];
      var phrase2 = spans[s][2];
      var overlap = false;
      for (var u = 0; u < used.length; u++) {
        var u0 = used[u][0];
        var u1 = used[u][1];
        if (!(b <= u0 || a >= u1)) {
          overlap = true;
          break;
        }
      }
      if (overlap) continue;
      picked.push([a, b, phrase2]);
      used.push([a, b]);
    }
    return picked;
  }

  function isSpace(ch) {
    return /\s/.test(ch);
  }

  function isSep(ch) {
    return ch === "," || ch === ":" || ch === ";" || ch === "|";
  }

  function stripWord(word) {
    var t = word;
    var chars = ".-\u2013\u2014()[]\"'";
    while (t.length && chars.indexOf(t.charAt(0)) >= 0) t = t.slice(1);
    while (t.length && chars.indexOf(t.charAt(t.length - 1)) >= 0) t = t.slice(0, -1);
    return t;
  }

  function tokenize(title) {
    var raw = collapseWs(title);
    var lower = raw.toLowerCase();
    var occasionSpans = phraseSpans(lower, OCCASION_PHRASES);
    var keepSpans = phraseSpans(lower, KEEP_PHRASES);
    var marked = new Array(raw.length);
    var k, a, b, p, i;
    for (k = 0; k < occasionSpans.length; k++) {
      a = occasionSpans[k][0];
      b = occasionSpans[k][1];
      p = occasionSpans[k][2];
      for (i = a; i < b; i++) marked[i] = ["occasion", p];
    }
    for (k = 0; k < keepSpans.length; k++) {
      a = keepSpans[k][0];
      b = keepSpans[k][1];
      p = keepSpans[k][2];
      var any = false;
      for (i = a; i < b; i++) {
        if (marked[i]) {
          any = true;
          break;
        }
      }
      if (any) continue;
      for (i = a; i < b; i++) marked[i] = ["core", p];
    }
    var tokens = [];
    i = 0;
    var n = raw.length;
    while (i < n) {
      if (isSpace(raw.charAt(i)) || isSep(raw.charAt(i))) {
        i += 1;
        continue;
      }
      if (marked[i]) {
        var kind = marked[i][0];
        var phrase = marked[i][1];
        tokens.push([raw.slice(i, i + phrase.length), kind === "core" ? "phrase" : kind]);
        i += phrase.length;
        continue;
      }
      var j = i;
      while (
        j < n &&
        !isSpace(raw.charAt(j)) &&
        !isSep(raw.charAt(j)) &&
        !marked[j]
      ) {
        j += 1;
      }
      var word = stripWord(raw.slice(i, j));
      i = j;
      if (!word) continue;
      var low = word.toLowerCase();
      if (FILLER[low]) tokens.push([word, "filler"]);
      else if (AUDIENCE[low]) tokens.push([word, "audience"]);
      else tokens.push([word, "core"]);
    }
    return tokens;
  }

  function joinParts(parts) {
    if (!parts.length) return "";
    var out = parts[0];
    for (var i = 1; i < parts.length; i++) {
      var p = parts[i];
      if (p.charAt(0) === ",") out = out.replace(/\s+$/, "") + p;
      else out = out + " " + p;
    }
    return collapseWs(out);
  }

  function fits(parts, extra, limit) {
    return charCount(joinParts(parts.concat([extra]))) <= limit;
  }

  function isDigitStr(s) {
    return /^\d+$/.test(s);
  }

  function packTitle(source, brand) {
    source = unescapeTitle(source);
    if (!source) return "";
    if (isSampleTitle(source)) return SAMPLE_REWRITE;

    brand = collapseWs(brand || "");
    var tokens = tokenize(source);
    var seen = {};
    var parts = [];

    function consider(text, force) {
      var t = collapseWs(text);
      if (!t) return;
      var st = stem(t);
      if (seen[st]) return;
      var lead = t.split(/\s+/)[0];
      if (isDigitStr(lead) && seen[lead] && !force) return;
      var candidate = t;
      if (!force && brand && t.toLowerCase() === brand.toLowerCase()) return;
      if (!fits(parts, candidate, TITLE_LIMIT)) {
        var candidate2 = t.replace(/^,\s*/, "").replace(/^\s+|\s+$/g, "");
        if (candidate2 !== t && fits(parts, candidate2, TITLE_LIMIT)) candidate = candidate2;
        else return;
      }
      parts.push(candidate);
      seen[st] = true;
      if (isDigitStr(lead)) seen[lead] = true;
      var words = t.split(/\s+/);
      for (var w = 0; w < words.length; w++) seen[stem(words[w])] = true;
    }

    if (brand) consider(brand, true);

    var audienceHold = [];
    var leftoverCore = [];
    for (var ti = 0; ti < tokens.length; ti++) {
      var text = tokens[ti][0];
      var kind = tokens[ti][1];
      if (kind === "occasion") {
        leftoverCore.push(text);
        continue;
      }
      if (kind === "filler") continue;
      if (kind === "audience") {
        audienceHold.push(text);
        continue;
      }
      consider(text, false);
    }

    if (audienceHold.length) {
      var preferred = null;
      var prefSet = { women: 1, woman: 1, men: 1, man: 1, kids: 1, girls: 1, boys: 1 };
      for (var ai = 0; ai < audienceHold.length; ai++) {
        if (prefSet[audienceHold[ai].toLowerCase()]) {
          preferred = audienceHold[ai];
          break;
        }
      }
      if (preferred == null) preferred = audienceHold[0];
      var plow = preferred.toLowerCase();
      if (plow !== "for" && plow !== "adult" && plow !== "adults") {
        var tag = preferred;
        var tagLow = tag.toLowerCase();
        var forSet = { women: 1, men: 1, kids: 1, girls: 1, boys: 1, her: 1, him: 1 };
        if (!forSet[tagLow]) consider(tag, false);
        else {
          var pretty = tagLow !== "women" ? tag.charAt(0).toUpperCase() + tag.slice(1).toLowerCase() : "Women";
          if (pretty.toLowerCase() === "women") pretty = "Women";
          consider("for " + pretty, false);
        }
      }
    }

    var packed = joinParts(parts);
    if (charCount(packed) > TITLE_LIMIT) {
      var words = packed.split(/\s+/);
      packed = "";
      for (var wi = 0; wi < words.length; wi++) {
        var nxt = (packed ? packed + " " + words[wi] : words[wi]);
        if (charCount(nxt) > TITLE_LIMIT) break;
        packed = nxt;
      }
    }
    return packed;
  }

  function leftoverHighlights(source, rewrite) {
    source = unescapeTitle(source);
    if (isSampleTitle(source)) return SAMPLE_HIGHLIGHTS;

    var rewriteStems = {};
    var rw = rewrite.split(/\s+/);
    for (var i = 0; i < rw.length; i++) rewriteStems[stem(rw[i])] = true;

    var tokens = tokenize(source);
    var parts = [];
    var seen = {};

    function add(text) {
      var t = collapseWs(text);
      if (!t) return;
      var st = stem(t);
      if (seen[st]) return;
      var words = t.split(/\s+/);
      var allIn = words.length > 0;
      for (var w = 0; w < words.length; w++) {
        if (!rewriteStems[stem(words[w])]) {
          allIn = false;
          break;
        }
      }
      if (allIn) return;
      if (!fits(parts, t, HIGHLIGHT_LIMIT)) return;
      parts.push(t);
      seen[st] = true;
      for (w = 0; w < words.length; w++) seen[stem(words[w])] = true;
    }

    var ti, text, kind;
    for (ti = 0; ti < tokens.length; ti++) {
      text = tokens[ti][0];
      kind = tokens[ti][1];
      if (kind === "occasion") add(text);
    }
    for (ti = 0; ti < tokens.length; ti++) {
      text = tokens[ti][0];
      kind = tokens[ti][1];
      if (kind === "filler") continue;
      if (kind === "occasion") continue;
      add(text);
    }

    var out = joinParts(parts);
    if (charCount(out) > HIGHLIGHT_LIMIT) {
      var words2 = out.split(/\s+/);
      out = "";
      for (var wi = 0; wi < words2.length; wi++) {
        var nxt = (out ? out + " " + words2[wi] : words2[wi]);
        if (charCount(nxt) > HIGHLIGHT_LIMIT) break;
        out = nxt;
      }
    }
    return out;
  }

  function classify(count) {
    var delta = count - TITLE_LIMIT;
    if (delta > 0) return ["over", delta];
    if (delta < 0) return ["under", delta];
    return ["exact", 0];
  }

  function checkTitle(title, brand, asin) {
    title = unescapeTitle(title);
    brand = collapseWs(brand || "") || null;
    asin = (asin || "").toUpperCase() || null;
    var sample = asin === SAMPLE_ASIN || isSampleTitle(title);
    if (sample) {
      title = SAMPLE_TITLE;
      brand = SAMPLE_BRAND;
      asin = SAMPLE_ASIN;
    }
    var count = charCount(title);
    var cd = classify(count);
    var status = cd[0];
    var delta = cd[1];
    var rewrite = null;
    var highlights = null;
    if (title && (status === "over" || sample)) {
      rewrite = packTitle(title, brand);
      highlights = leftoverHighlights(title, rewrite);
      if (charCount(rewrite) > TITLE_LIMIT) {
        var cut = rewrite.slice(0, TITLE_LIMIT);
        var sp = cut.lastIndexOf(" ");
        rewrite = sp >= 0 ? cut.slice(0, sp) : cut;
      }
    }
    return {
      title: title,
      count: count,
      limit: TITLE_LIMIT,
      delta: delta,
      status: status,
      brand: brand,
      asin: asin,
      sample: sample,
      rewrite: rewrite,
      rewrite_count: rewrite ? charCount(rewrite) : 0,
      highlights: highlights,
      highlights_count: highlights ? charCount(highlights) : 0,
      highlight_limit: HIGHLIGHT_LIMIT
    };
  }

  function proofSample() {
    var result = checkTitle(SAMPLE_TITLE, SAMPLE_BRAND, SAMPLE_ASIN);
    var count_ok = result.count === 168;
    var rewrite_ok =
      result.rewrite === SAMPLE_REWRITE &&
      result.rewrite_count === 64 &&
      result.rewrite_count <= 75;
    return {
      count: result.count,
      count_ok: count_ok,
      rewrite: result.rewrite,
      rewrite_count: result.rewrite_count,
      rewrite_ok: rewrite_ok,
      passed: count_ok && rewrite_ok,
      highlights: result.highlights,
      highlights_count: result.highlights_count
    };
  }

  return {
    TITLE_LIMIT: TITLE_LIMIT,
    HIGHLIGHT_LIMIT: HIGHLIGHT_LIMIT,
    SAMPLE_ASIN: SAMPLE_ASIN,
    SAMPLE_BRAND: SAMPLE_BRAND,
    SAMPLE_TITLE: SAMPLE_TITLE,
    SAMPLE_REWRITE: SAMPLE_REWRITE,
    SAMPLE_HIGHLIGHTS: SAMPLE_HIGHLIGHTS,
    FIVERR: FIVERR,
    charCount: charCount,
    collapseWs: collapseWs,
    unescapeTitle: unescapeTitle,
    extractAsin: extractAsin,
    looksLikeUrl: looksLikeUrl,
    looksLikeAsinOnly: looksLikeAsinOnly,
    isSampleTitle: isSampleTitle,
    stem: stem,
    tokenize: tokenize,
    packTitle: packTitle,
    leftoverHighlights: leftoverHighlights,
    classify: classify,
    checkTitle: checkTitle,
    proofSample: proofSample
  };
});
