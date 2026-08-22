# Contributing games to the Moss database

Add or edit entries in [`src/moss/data/games_db.yaml`](src/moss/data/games_db.yaml):

```yaml
- id: my-game
  names: ["My Game", "MyGame"]
  steam_appid: 12345        # 0 if unknown
  required_verbs: [vcrun2019, vcrun2022, d3dcompiler_47]
  notes: "Short tip for players"
  anti_cheat: none          # none | eac | battleye
```

`required_verbs` are [winetricks](https://github.com/Winetricks/winetricks) verb names. Prefer well-known verbs already listed in Settings → game Configure.

Open a PR against `main` with a short note on how you verified the verbs.
