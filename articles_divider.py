
import os
import json
import re


def slugify(name: str) -> str:
	if not name:
		return "unknown"
	s = name.strip().lower()
	s = re.sub(r"[^a-z0-9]+", "_", s)
	s = re.sub(r"_+", "_", s)
	return s.strip("_") or "unknown"


def divide_by_outlet(articles_path: str, out_dir: str = None) -> None:
	if out_dir is None:
		out_dir = os.path.dirname(articles_path)
	os.makedirs(out_dir, exist_ok=True)

	with open(articles_path, "r", encoding="utf-8") as f:
		data = json.load(f)

	# Expecting a list of article objects
	groups = {}
	for item in data:
		outlet = item.get("outlet") or item.get("source") or "unknown"
		key = slugify(outlet)
		groups.setdefault(key, {"outlet": outlet, "articles": []})["articles"].append(item)

	for key, payload in groups.items():
		out_path = os.path.join(out_dir, f"{key}.json")
		with open(out_path, "w", encoding="utf-8") as f:
			json.dump(payload, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
	base = os.path.join(os.path.dirname(__file__), "articles")
	in_file = os.path.join(base, "articles.json")
	if not os.path.isfile(in_file):
		print(f"Input file not found: {in_file}")
	else:
		divide_by_outlet(in_file, out_dir=base)
		print("Done.")
