from io import BytesIO

import pandas as pd


def dataframe_to_xlsx(frame: pd.DataFrame, sheet_name: str = "analysis") -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return output.getvalue()
