/* slug -> direct audio URL.

   Two properties are non-negotiable, and each has broken the vault once:

   1. An honest audio Content-Type. GitHub *Releases* serve every asset as
      application/octet-stream with a Content-Disposition: attachment header.
      Android Chrome sniffs past that; WebKit never does — and Chrome on an
      iPhone is WebKit. Confirmed on a real device (iOS 18.6, 2026-08-18):
      MediaError.code 4, "this browser refused the file".
   2. HTTP range support. Without it, clicking a timecode re-downloads the
      whole three-hour recording instead of seeking into it.

   GitHub *Pages* — the same site the vault is published on — satisfies both:
   audio/mp3, accept-ranges: bytes, no attachment header. So the recordings
   now live beside the vault rather than in a release.

   Google Drive was ruled out earlier: files over 100 MB return a virus-scan
   HTML page instead of audio.

   Sessions 13 and 16 were re-encoded from the original WAV masters at 48 kbps
   to fit git's hard 100 MB per-file limit; the other three are byte-identical
   to the originals. */

const AU = "https://dosenft.github.io/dwk-vault/audio/";

const AUDIO_URLS={
 "caremall-recon-and-grand-rebirth-pact": AU+"s14-caremall.mp3",          /* Session 16 */
 "city-festival-arrival":                 AU+"s13-city-festival.mp3",     /* Session 15 */
 "ponzis-oath-and-feywild-quest":         AU+"s12-ponzis-oath.mp3",       /* Session 14 */
 "festival-planning-night-before":        AU+"s11-festival-planning.mp3", /* Session 13 */
 "journey-to-vattenheim-misty-fortress":  AU+"s10-vattenheim.mp3"         /* Session 12 */
};

