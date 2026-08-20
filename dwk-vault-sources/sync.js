/* Where the shared vault lives. The key below is a public, read-and-append-only
   key — it is meant to ship in the page. What it can do is fixed in the
   database itself: read the change log, add to the change log. It cannot
   change or delete a single row that is already there. */
const SUPA={
 url:'https://olsoszyirfbqdinczlvc.supabase.co',
 key:'sb_publishable_NE6C29qOEufeomhpWMgaGw_64E89SG3'
};
/* Rows already folded into the copy of the campaign baked into this file.
   The save routine rewrites this number, so republishing never double-applies
   a change that is already in the page. */
let BASE_EDIT=0;
