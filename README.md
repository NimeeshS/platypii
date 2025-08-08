# 🦫  PlatyPII

PlatyPII is a modular, extensible Python framework for detecting and anonymizing Personally Identifiable Information (PII) in unstructured text. PlatyPII makes it easy to integrate  PII detection into your applications.

## 🚀 Features

    🔍 PII Detection: Detects emails, phone numbers, names, addresses, SSNs, and more.

    🧠 Hybrid Detection Engine: Combines rule-based regex detectors with NLP-based detectors (spaCy).

    🛡 Anonymization Options: Supports multiple anonymization methods: mask, redact, hash, replace, and synthetic.

    ⚙️ Configurable Settings: Fine-tune detection thresholds, enable/disable PII types, and customize output.

    📦 Batch Processing: Run detection and anonymization across multiple documents at once.

    🧪 Test Suite: Built-in test runner to verify core functionality, configuration, and individual detectors.

📦 Installation

git clone https://github.com/NimeeshS/platypii.git

cd platypii

pip install -r requirements.txt

    ⚠️ Make sure you're using Python 3.7+.

🧠 How It Works

PlatyPII works by orchestrating multiple detectors that each scan text for specific kinds of PII. It then applies a selected anonymization method to redact or transform the matched values.
Architecture Overview:

Your Text → PIIEngine → Detectors → Anonymized Text

🧪 Running Tests

You can verify the functionality of the system using the provided test.py script:

python3 test.py

Test Coverage:

    ✅ Basic PII detection + anonymization

    ✅ Batch document processing

    ✅ Configuration system

    ✅ Individual detector testing (Regex + NLP)

🛠 Usage
Detecting and Masking PII
```
from platypii import detect_pii, mask_pii

text = "Email me at alice@example.com or call 123-456-7890."
matches = detect_pii(text)

for match in matches:
    print(f"{match.pii_type}: {match.value} (confidence: {match.confidence:.2f})")

masked = mask_pii(text)
print(masked)

Using the PIIEngine

from platypii.core.engine import PIIEngine

engine = PIIEngine()
result = engine.process_text("SSN: 123-45-6789", anonymize=True, method="redact")

print(result["anonymized_text"])
```

🔧 Configuration

The system is configurable via the Config class:
```
from platypii.config import Config

config = Config()
print(config.get("detection.confidence_threshold"))  # Default threshold
config.set("detection.confidence_threshold", 0.9)    # Update threshold
```
🧩 Supported Anonymization Methods
Method	     Description

mask	     Replaces characters with *  
redact	     Replaces values with [REDACTED]  
hash	     Replaces values with SHA-256 hash  
replace	     Replaces with dummy placeholder values  
synthetic    Replaces with realistic synthetic data (optional)