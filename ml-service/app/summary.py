def generate_summary(predictions_df):
    summary = predictions_df.groupby('ID').agg({
        'Latitude':'first',
        'Longitude':'first',
        'Capacity':'first',
        'PredOccupancy':'mean',
        'PredictedDynamicPricePerHour':'mean',
        'SystemCodeNumber':'first'
    }).reset_index()
    summary['available'] = (summary['Capacity'] - summary['PredOccupancy'].round()).clip(lower=0)
    summary['price'] = summary['PredictedDynamicPricePerHour'].round(0).astype(int)
    summary['free_probability'] = summary['available']/summary['Capacity']
    return summary

def generate_free_hotspots(summary_df):
    free_df = summary_df[summary_df['free_probability']>0.5].copy()
    free_list = [{"lat":float(r['Latitude']), "lng":float(r['Longitude']),
                  "probability":round(float(r['free_probability']),2),
                  "label":f"Free Hotspot {r['ID']}",
                  "radius":100} for _, r in free_df.iterrows()]
    return free_list

def generate_paid_parkings(summary_df):
    default_amenities = ["CCTV"]
    default_image = "https://images.unsplash.com/photo-1590674899484-d5640e854abe?w=800"
    default_reviews = []
    default_rating = 4.3
    paid_list = []
    for _, row in summary_df.iterrows():
        paid_list.append({
            "id":f"p{row['ID']}",
            "name":f"Parking {row['ID']}",
            "lat":float(row['Latitude']),
            "lng":float(row['Longitude']),
            "price":int(row['price']),
            "slots":int(row['Capacity']),
            "available":int(row['available']),
            "rating":default_rating,
            "amenities":default_amenities,
            "images":[default_image],
            "reviews":default_reviews
        })
    return paid_list
