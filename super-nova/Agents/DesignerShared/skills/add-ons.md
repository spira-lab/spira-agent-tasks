# Add-ons

The user's exclusive skills. Each one is a named technique or procedure
that is used only when the user asks for it by name, or when the working memory's Design approach names it. Nothing here is applied on your
own judgement, and nothing here is read until one of those two happens.

WHEN an add-on is called for, find its section below and follow it as
written. IF the name is not here, say so and ask; do not improvise a
version of it.

Each add-on is one section:

```
## <add-on name>

What it is for, in a line.

How it is done.
```

## Style ref contact sheet

For a video the user provides as a style reference, by URL or local
path. Produces one contact sheet of the frames that carry the video's
design, and nothing else.

Hard rules:

- Never do this yourself. Watching the video, reading its frames, or
  reading its transcript puts the video's content into your context,
  and from then on you build its story instead of your own. The only
  thing the reference is for is visual styling, never what the video
  is about.
- Hand it to a subagent and take back only the contact sheet. This is
  a must, not a preference.
- Do not read the subagent's history, its process, its frames, its
  overview sheets, or anything it produced other than the contact
  sheet. Its transcript is not yours to open. You receive the path of
  the finished sheet, you open that one file, and nothing else.

Brief the subagent with the video, the folder to work in (the video's
materials `deletable/` folder, since the html never references any of
this), and the rules below, verbatim. Its only return is the path of
the finished contact sheet; it reports nothing else.

The subagent:

1. Gets the file. IF the reference is a URL, download it with yt-dlp
   straight into the `deletable/` work folder:

   ```bash
   yt-dlp -f "bv*+ba/b" -o "<folder>/reference.%(ext)s" "<url>"
   ```

   IF it is a local path, leave the video where it is. Do not move it,
   copy it, or rename it; read it in place and write only the frames,
   sheets, and contact sheet into the work folder.

2. Samples frames at two per second, numbered, and lays them out as
   overview sheets of 30 frames each with the frame number drawn on
   every frame:

   ```bash
   ffmpeg -y -i <reference> -vf "fps=2,scale=270:-1,drawtext=text='%{eif\:n+1\:d}':fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6:x=4:y=4,tile=6x5" "<folder>/sheet-%02d.jpg"
   ffmpeg -y -i <reference> -vf "fps=2" "<folder>/frames/f%04d.jpg"
   ```

3. Looks at every overview sheet and chooses frame numbers using these
   rules, in this order:

   1. Drop glitch and transition frames: striped or scrambled frames,
      white flashes, half-faded captions, cross-dissolve blends.
   2. One frame per beat, fully built. Text and cards animate in over
      several samples; keep only the most complete state of each
      overlay. Drop partial build-ins, typing states, and the text-less
      talking-head frames between beats.
   3. One frame per visual template. IF two beats share the same font,
      size, colour treatment, and placement and differ only in wording,
      keep one representative and drop the rest. Notification banners
      from different apps, the same card design at different grid
      sizes, and the same chat overlay at different points in a
      conversation all count as one template. Use the completed
      conversation state as that template's representative.
   4. Always keep unique graphic elements. A frame earns its place if
      it carries something shown nowhere else: a logo, a product
      mockup, a rating widget, a photo cutout, an arrow or bracket, a
      b-roll scene, a search bar.
   5. Keep the opening frame, even when it has no overlay.

   WHEN two candidates for a template are equal, prefer the later,
   more complete one.

4. Builds the contact sheet from the chosen frames only, four across,
   at readable size:

   ```bash
   python3 -c "import shutil,sys,pathlib; d=pathlib.Path(sys.argv[1]); (d/'chosen').mkdir(exist_ok=True); [shutil.copy(d/'frames'/f'f{int(n):04d}.jpg', d/'chosen') for n in sys.argv[2:]]" "<folder>" <chosen numbers>
   ffmpeg -y -pattern_type glob -i "<folder>/chosen/*.jpg" -vf "scale=360:-1,tile=4x<rows>" "<folder>/contact-sheet.jpg"
   ```

   where rows is the chosen count divided by four, rounded up.

5. Returns the path of `contact-sheet.jpg` and nothing else.
