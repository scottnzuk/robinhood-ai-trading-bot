# My Transformers Extensions

This package is designed to **safely extend and customize** the [Transformers](https://github.com/huggingface/transformers) library **without modifying the original cloned repository**.

---

## Why use this?

- **Keep the upstream `transformers` repo pristine** for easy updates or re-cloning.
- **Add new features, bug fixes, or wrappers** without risk.
- **Override or patch existing classes and functions** in a clean, maintainable way.
- **Organize your own NLP logic** separately from the vendor code.

---

## How to use

1. **Import your extension package instead of `transformers` directly:**

```python
import my_transformers_extensions as mytf

# Call your wrapper or extended functions
mytf.my_load_model("bert-base-uncased")
```

2. **Add your own modules**

Create new files like `model_wrappers.py`, `tokenizer_patches.py`, etc., inside this folder.

3. **Extend or override**

Wrap or override original classes or functions:

```python
import transformers

def my_custom_tokenizer(name, **kwargs):
    # Add your logic here
    return transformers.AutoTokenizer.from_pretrained(name, **kwargs)
```

4. **Keep your changes safe**

Since this folder is outside the cloned repo, you can update or delete the original `transformers` anytime without losing your work.

---

## Example structure

```
my_transformers_extensions/
├── __init__.py
├── model_wrappers.py
├── tokenizer_patches.py
├── training_extensions.py
└── README.md
```

---

## Notes

- You can also create **subpackages** inside this folder if needed.
- Remember to update your imports to use your extensions.
- Follow best practices for packaging if you want to distribute or reuse this code.

---

## License

Your own license here.