import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file (assuming your data is in a CSV file with columns Name, Distance, Value)
df = pd.read_csv("picks.csv", header=None, names=["Name", "Distance", "Age"])

# Count occurrences of each name
name_counts = df["Name"].value_counts()

# Filter names that appear more than once
duplicates = df[df["Name"].isin(name_counts[name_counts > 1].index)]

print(duplicates)


# Count occurrences of each name
name_counts = df["Name"].value_counts()

# Filter names that appear more than once
name_counts_filtered = name_counts[name_counts > 1]

# Plot the bar chart
plt.figure(figsize=(10, 5))
name_counts_filtered.plot(kind="bar", color="skyblue")
plt.xlabel("Name")
plt.ylabel("Count")
plt.title("Frequency of Names (Only Showing Those Appearing More Than Once)")
plt.xticks(rotation=45, ha="right")  # Rotate labels for readability
plt.grid(axis="y", linestyle="--", alpha=0.7)

# Show the plot
plt.show()
