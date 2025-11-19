import pandas as pd
from pathlib import Path


def extract_sentences_and_labels(file_content):
    """Return (sentences, labels) parsed from a file content where each line
    contains a sentence and a label separated by the last '@' character.
    """
    sentences = []
    labels = []

    lines = file_content.strip().split('\n')

    for line in lines:
        if '@' in line:
            parts = line.rsplit('@', 1)
            if len(parts) == 2:
                sentence = parts[0].strip()
                label = parts[1].strip()
                sentences.append(sentence)
                labels.append(label)

    return sentences, labels


def process_files(file_paths, out_dir=None, drop_duplicate_rows=False):
    """Process a list of text files and write per-file CSVs and a unioned CSV.

    - file_paths: iterable of Path or str pointing to the text files.
    - out_dir: optional Path to write CSVs into (defaults to the directory of the text files).
    - drop_duplicate_rows: if True, drop exact duplicate (sentence,label) rows in the union.
    """
    dataframes = []

    for fp in file_paths:
        p = Path(fp)
        if not p.exists():
            print(f"Warning: source file not found: {p}")
            continue

        # Try reading as utf-8, fallback to latin-1, otherwise replace undecodable
        try:
            content = p.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = p.read_text(encoding='latin-1')
                print(f"Read {p.name} with latin-1 fallback")
            except Exception:
                # Last resort: read bytes and decode with replacement to avoid crashing
                content = p.read_bytes().decode('utf-8', errors='replace')
                print(f"Read {p.name} with bytes-decode fallback (errors replaced)")
        sentences, labels = extract_sentences_and_labels(content)

        df = pd.DataFrame({
            'sentence': sentences,
            'label': labels,
            'source_file': [p.name] * len(sentences)
        })

        # Ensure output directory
        target_dir = Path(out_dir) if out_dir is not None else p.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        per_file_csv = target_dir / f"extracted_sentences_{p.name}.csv"
        df.to_csv(per_file_csv, index=False, encoding='utf-8')
        print(f"Wrote {len(df)} rows to {per_file_csv}")

        dataframes.append(df)

    if not dataframes:
        print("No dataframes created. Exiting.")
        return None

    union_df = pd.concat(dataframes, ignore_index=True)
    if drop_duplicate_rows:
        before = len(union_df)
        union_df = union_df.drop_duplicates(subset=['sentence', 'label'])
        after = len(union_df)
        print(f"Dropped {before-after} duplicate rows from unioned dataset")

    # Write the unioned CSV in the same directory as the first file (or out_dir if provided)
    union_target_dir = Path(out_dir) if out_dir is not None else Path(file_paths[0]).parent
    union_csv = Path(union_target_dir) / 'all_sentences_unioned.csv'
    union_df.to_csv(union_csv, index=False, encoding='utf-8')
    print(f"Wrote unioned dataset with {len(union_df)} rows to {union_csv}")

    return union_df


if __name__ == '__main__':
    # Determine dataset directory (this file lives in the dataset/ folder)
    base_dir = Path(__file__).parent

    # List of source text files to include
    source_files = [
        base_dir / 'Sentences_50Agree.txt',
        base_dir / 'Sentences_66Agree.txt',
        base_dir / 'Sentences_75Agree.txt',
        base_dir / 'Sentences_AllAgree.txt',
    ]

    # Run processing. Set drop_duplicate_rows=True if you want to remove exact duplicates.
    process_files(source_files, out_dir=base_dir, drop_duplicate_rows=False)