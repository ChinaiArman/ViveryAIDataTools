import argparse
import pandas as pd




def create_jsonl_file(df, path, input_column, output_column):
    input = list(df[input_column])
    output = list(df[output_column])

    with open(path, 'w') as jsonl_file:
        for i in range(len(input)):
            jsonl_file.write('{"prompt": "' + str(input[i]) + '", "completion": "' + str(output[i]) + '%' + '%"}\n') 


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create data visualizations for a Pre-Validated file")

    parser.add_argument("input_file", action="store", help="The file to validate.")
    parser.add_argument("output_file", action="store", help="To name the PDF and customize to the specific Network")
    parser.add_argument("input_column", action="store", help="The file to validate.")
    parser.add_argument("output_column", action="store", help="To name the PDF and customize to the specific Network")

    args = parser.parse_args()

    df = pd.read_csv(args.input_file)

    create_jsonl_file(df, args.output_file, args.input_column, args.output_column)
