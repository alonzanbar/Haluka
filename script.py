from tkinter import Tk, filedialog
from openpyxl import Workbook
from maps import geocode_missing_and_save, get_optimized_address_order
from ml import *

api_key = 'AIzaSyDXFcbcYfJYZVNbgiSB6MSLde2SHxVUekY'
sheet_name = "29.8.25"
origin_address = "מטווח אריאל"
output_file = "delivery_routes_1_8_{}.xlsx"



def prompt_for_excel_file():
    Tk().withdraw()
    filename = filedialog.askopenfilename(
        title="Select Excel file",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    return filename


def load_recipients(filename):
    df = pd.read_excel(filename,sheet_name)
    expected_cols = {'name', 'address', 'phone', 'packages'}
    df = geocode_missing_and_save(df.iloc[:,:].copy(), api_key,'address','latitude','longitude',filename,sheet_name)
    if not expected_cols.issubset(df.columns):
        raise ValueError(f"The file must contain columns: {expected_cols}")
    return df


def prompt_for_num_groups():
    while True:
        try:
            num_groups = int(input("How many delivery groups to create? "))
            if num_groups > 0:
                return num_groups
        except ValueError:
            pass
        print("Please enter a positive integer.")


def process_group(group_df, group_id, api_key, origin_address, writer):
    print(f"\n📦 Group {group_id + 1}")

    # Step 1: Build full address list
    recipient_addresses = group_df['address'].tolist()
    full_address_list = [origin_address] + recipient_addresses + [origin_address]

    # Step 2: Get optimized order from Google
    try:
        optimized_addresses = get_optimized_address_order(full_address_list, api_key)
        delivery_addresses = optimized_addresses[1:-1]  # exclude fixed origin
        group_df = group_df.set_index('address').loc[delivery_addresses].reset_index()
    except Exception as e:
        print(f"⚠️ Failed to optimize route: {e}")
        delivery_addresses = recipient_addresses  # fallback

    # Step 3: Print optimized delivery route
    for idx, row in group_df.iterrows():
        print(f"  {idx+1}. {row['name']} - {row['address']} ({row['packages']} packages)")

    # Step 4: Generate Google Maps link
    map_link = generate_google_maps_link([origin_address] + delivery_addresses + [origin_address])
    print(f"  🗺️  Google Maps Route: {map_link}")

    # Step 5: Optional debug – show distance matrix
    coords = group_df[['latitude', 'longitude']].values.tolist()
    dist_matrix = create_distance_matrix(coords)
    print("  Distance matrix (km):")
    for row in dist_matrix:
        print("  ", ["{:.2f}".format(d) for d in row])

    # Step 6: Export to Excel (add route order column)
    group_df.insert(0, 'Route Order', range(1, len(group_df) + 1))
    sheet_name = f"Group {group_id + 1}"
    group_df.to_excel(writer, sheet_name=sheet_name, index=False)


def process_all_groups(df, num_groups):
    # OPTIONAL: delete old file if it exists to avoid stale errors
    import os
    if os.path.exists(output_file):
        os.remove(output_file)
    df = distribute_evenly(df, num_groups)
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='w') as writer:
        for group_id in sorted(df['group'].unique()):
            group_df = df[df['group'] == group_id].reset_index(drop=True)
            process_group(group_df, group_id, api_key, origin_address, writer)


def main():
    print("📄 Meal Distribution Planner 📄")

    filename = prompt_for_excel_file()
    if not filename:
        print("No file selected. Exiting.")
        return

    try:
        df = load_recipients(filename)
    except Exception as e:
        print(e)
        print(f"❌ Error: {e}")
        return

    print(f"\n✅ Loaded {len(df)} recipients from {filename}\n")

    num_groups = prompt_for_num_groups()
    process_all_groups(df, num_groups)

    print("\n🎉 Done!")


if __name__ == "__main__":
    main()