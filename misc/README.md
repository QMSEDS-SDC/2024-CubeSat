# Running Test Files

## **Overview**

This project uses Python's module-based execution for running test files. The test files are executed as modules using the `python3` command-line interface, ensuring clean imports and a well-structured codebase.

## **Running Tests**

To execute a specific test file, use the following format:

```bash
python3 -m test.<test-type>.<test>
```

## **Example**

To run the test file `detect_test.py` located in the `test/image_detection_tests` directory:

```bash
python3 -m test.image_detection_tests.detect_test
```

## **Project Structure**

Below is an example of the project directory structure to illustrate where test files are located:

```plaintext
project/
│
├── src/
│   ├── my_package/
│   │   ├── __init__.py
│   │   ├── foo.py
│   │
│   └── __init__.py
│
└── test/
    ├── __init__.py
    ├── image_detection_tests/
    │   ├── __init__.py
    │   ├── detect_test.py
    │
    └── other_test_types/
        ├── __init__.py
        ├── example_test.py
```

---

#### **Notes**

1. Run all commands from the root directory of the project.

---

#### **Advantages of This Approach**

- Maintains clean import paths for source and test files.
- Avoids modifying `PYTHONPATH` or using external testing frameworks.
