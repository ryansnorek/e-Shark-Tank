import pandas as pd
import math
import statistics
import random
from functools import reduce


def getCustomerData(customers):

    customerData = {}
    totalCustomers = len(customers)
    recurringCustomers = 0

    # Count how many customers returned more than 3 times
    # and calculate retention rate
    for c in customers:

        if (customers[c] > 3):
            recurringCustomers += 1

    retentionRate = round(
        (totalCustomers - recurringCustomers) / totalCustomers, 2)

    # Load customer data and return
    customerData['Total Customers'] = totalCustomers
    customerData['Retention Rate'] = retentionRate
    customerData['Recurring Customers'] = recurringCustomers

    return customerData


def getRiskScore(customers, earnings):
    # Use weighted averages to create a score that gauges risk level based on
    # customer retention, customer volume, and earnings volatility

    riskScoreData = {}
    # Assign weight % and values
    customerVolumeWeight = 0.4
    retentionWeight = 0.5
    volatilityWeight = 0.1

    customerVolume = customers['Total Customers']
    retention = customers['Retention Rate']
    volatility = earnings['Volatility']

    # Customer volume based on how many figures in total number of customers
    # Ex: 10,000 (5 figures) vs 10M (8 figures)
    customerVolume = len(str(customerVolume)) / 10

    # Calculate scores (input * weight)
    # Subtract from 1 if the benefit of the input is inverted
    # Ex: High retention is positive, High volatility is negative
    customerVolumeScore = round(1 - (customerVolume * customerVolumeWeight), 2)
    retentionScore = round(1 - (retention * retentionWeight), 2)
    volatilityScore = round(volatility * volatilityWeight, 2)

    # Calculate final risk score
    riskScore = ((customerVolumeScore * customerVolumeWeight) +
                 (retentionScore * retentionWeight) +
                 (volatilityScore * volatilityWeight)) / 1

    def getMultiple(score):
        # EBIT multiple is based on the risk level
        multiple = 3

        if (score > 0.50):
            multiple = 2
            if (score > 0.75):
                multiple = 1

        return multiple

    riskScoreData['EBIT Multiple'] = getMultiple(riskScore)

    riskScoreData['Total Customers'] = customers['Total Customers']
    riskScoreData['Customer Volume Score'] = customerVolumeScore
    riskScoreData['Customer Volume Weight'] = customerVolumeWeight
    riskScoreData['Recurring Customers'] = customers['Recurring Customers']
    riskScoreData['Retention Rate'] = customers['Retention Rate']
    riskScoreData['Retention Score'] = retentionScore
    riskScoreData['Retention Weight'] = retentionWeight
    riskScoreData['Average Earnings'] = round(earnings['Average'])
    riskScoreData['Average Volatility'] = round(earnings['Volatility'], 2)
    riskScoreData['Volatility Score'] = volatilityScore
    riskScoreData['Volatility Weight'] = volatilityWeight
    riskScoreData['Risk Score'] = riskScore

    return riskScoreData


def getGrowthRates(earnings):
    rates = []
    growthRates = {}

    # Return growth rates of historical earnings
    for a, b in zip(earnings[::1], earnings[1::1]):
        r = (b - a) / a
        rates.append(r)

    growthRates['Min'] = min(rates)
    growthRates['Median'] = statistics.median(rates)
    growthRates['Max'] = max(rates)
    growthRates['Average'] = sum(rates) / len(rates)

    return growthRates


def getVolatility(ebit, average):
    volatility = 0

    # Variance = average of the sequence (EBIT - average EBIT)^2
    var = list(map(lambda e: pow((e - average), 2), ebit))
    variance = sum(var) / len(var)

    # Square root of variance
    standardDeviation = pow(variance, 0.5)

    # Volatility measured by the difference / average
    volatility = 1 - ((average - standardDeviation) / average)

    return volatility


def getEarningsData(sales):
    earningsData = {}

    # Assumption based on e-commerce industry average
    operatingProfitMargin = 0.4

    # Calculate assumed EBIT
    EBIT = []
    for year in sales:
        earnings = sales[year] * operatingProfitMargin
        EBIT.append(earnings)

    # Drop the most recent year since it is likely incomplete
    EBIT.pop(-1)

    # Calculate volatiliy using the ratio of the standard deviation
    # and the average earnings
    averageEarnings = sum(EBIT) / len(EBIT)
    volatility = getVolatility(EBIT, averageEarnings)

    earningsData['EBIT'] = EBIT
    earningsData['Average'] = averageEarnings
    earningsData['Volatility'] = volatility

    return earningsData


def getFinalValue(value):

    startupCosts = [
        # Shopify fee
        29,
        # Inventory
        1000,
        # Premium email
        5,
        # Web design
        150,
        # Incorporation
        500,
        # Logo design
        100,
        # Marketing
        100,
        # Warehousing
        1000
    ]

    # Add costs required to start the business from scratch
    finalValue = reduce(lambda x, y: x + y, startupCosts, value)

    return finalValue


def getEnterpriseValue():
    # Run the data through the model 10x to simulate different sales outcomes.
    # Return the average result
    values = []
    for i in range(10):
        financials = getFinancials(data['Sales'])
        values.append(financials['Enterprise Value'])

    enterpriseValue = sum(values) / len(values)

    return math.floor(enterpriseValue)


def getFinancials(sales):
    financials = {}

    # Variables for DCF model
    discountRate = 0.1
    corporateTaxRate = 0.21

    # Includes EBIT, average earnings, and volatility
    earningsData = getEarningsData(data['Sales'])

    # Includes total customers, recurring customers, and retention rate
    customerData = getCustomerData(data['Customers'])

    # Use the data to produce a weighted score out of 100 to gauge the risk
    # level and assign the approriate EBIT multiple
    riskScoreData = getRiskScore(customerData, earningsData)

    EBIT = earningsData['EBIT']
    EBITmultiple = riskScoreData['EBIT Multiple']
    growthRates = getGrowthRates(EBIT)

    # Start with the latest full year of earnings to calculate projections
    EBITprojections = []
    latestEarnings = EBIT[-1]
    EBITprojections.append(latestEarnings)

    # Apply a random growth rate between the minimum and median historical growth rate
    # Deduct taxes to get free cash flow projections
    cashFlowProjections = []

    for i in range(len(EBIT)):
        growthRate = random.uniform(growthRates['Min'], growthRates['Median'])

        projection = EBITprojections[i] + (EBITprojections[i] * growthRate)
        EBITprojections.append(projection)

        freeCashFlow = projection * (1 - corporateTaxRate)
        cashFlowProjections.append(freeCashFlow)

    # Drop the actual earnings leaving only the projected earnings in the list.
    EBITprojections.pop(0)

    # Terminal value = last EBIT projection x EBIT multiple
    terminalValue = math.floor(EBITprojections[-1] * EBITmultiple)

    # Add terminal value to the last cash flow projection
    cashFlowProjections[-1] = cashFlowProjections[-1] + terminalValue

    # Calculate NPV cash flows and enterprise value
    NPVcashFlows = []
    r = discountRate

    # NPV = CF / (1 + r)^n
    for i in range(len(cashFlowProjections)):
        n = i + 1
        NPV = cashFlowProjections[i] / pow((1 + r), n)
        NPVcashFlows.append(NPV)

    enterpriseValue = math.floor(sum(NPVcashFlows))

    # Load financials data
    financials['Earnings Data'] = earningsData
    financials['EBIT Projections'] = EBITprojections
    financials['Cash Flow Projections'] = cashFlowProjections
    financials['Terminal Value'] = terminalValue
    financials['NPV Cash Flows'] = NPVcashFlows
    financials['Enterprise Value'] = enterpriseValue
    financials['Risk Score'] = riskScoreData['Risk Score']
    financials['Risk Score Data'] = riskScoreData
    financials['Tax Rate'] = corporateTaxRate

    return financials


def getData(csvFile):
    # Return a dictionary object of sales and customer data
    data = {}
    df = pd.read_csv(csvFile)

    # Convert timestamp to date year and sales to a float
    df['ORDERED_AT'] = pd.to_datetime(df['ORDERED_AT']).dt.strftime('%Y')
    df['UNIT_PRICE'] = pd.to_numeric(df['UNIT_PRICE'])

    # Calculate total annual sales
    df['TOTAL_SALES'] = df['UNIT_PRICE'] * df['QUANTITY']
    sales = df.groupby('ORDERED_AT')['TOTAL_SALES'].sum().to_dict()
    data['Sales'] = sales

    # Calculate customer purchase frequency
    customers = df.groupby('CUSTOMER_ID').CUSTOMER_ID.count().to_dict()
    data['Customers'] = customers

    return data


# ************************************************************************************
#                                    START
# ************************************************************************************
# First get all the customer and sales data that will be used for the functions.
data = getData('order_lines.csv')

# Use a modified DCF model to process financial data.
# Modification includes a dynamic EBIT multiplier based on a "Risk Score".
# Risk Score is calculated using weighted rankings of 3 risk factors.
# Risk Factors include: Customer volume, retention, and earnings volatility.
# Assumptions include: EBIT multiplier, profit margin, and discount rate.
# Returns EBIT, EBIT & cash flow projections, NPV cash flows, terminal & enterprise values.
financials = getFinancials(data['Sales'])

# Attempting to create more accuracy by running the program 10 times using
# random growth rates within a range and return the average enterprise value.
# Range is between the minimum and median growth rates from earnings history.
enterpriseValue = getEnterpriseValue()

# Calculate and add estimated costs that would be required to start the business from scratch.
finalValue = getFinalValue(enterpriseValue)

# Calculate return on capital invested
latestEBIT = financials['Earnings Data']['EBIT'][-1]
taxRate = financials['Tax Rate']
returnOnCapital = round((latestEBIT * (1 - taxRate) / finalValue) * 100, 2)


def printRiskReport(data):
    # Print it all out!

    riskScore = data['Risk Score']
    print()
    print(' Risk Report')
    print('----------------------------------------')
    print('Total Customers: ', data['Total Customers'])
    print('Customer Volume: ', 100 -
          (data['Customer Volume Score'] * 100), '%')
    print('Score Weighting: ', 100 * data['Customer Volume Weight'], '%')
    print()
    print('Recurring Customers: ', data['Recurring Customers'])
    print('Retention Rate: ', data['Retention Rate'] * 100, '%')
    print('Score Weighting: ', 100 * data['Retention Weight'], '%')
    print()
    print('Average Annual Earnings: $', round(data['Average Earnings']))
    print('Average Volatility: ', 100 * data['Average Volatility'], '%')
    print('Score Weighting: ', 100 * data['Volatility Weight'], '%')
    print()
    print('Risk Score: ', round(riskScore, 2))
    print('----------------------------------------')


# Prints a report of the calculated risks and a final score
printRiskReport(financials['Risk Score Data'])

print('Business Valuation: $', finalValue)
print('Corporate Tax Rate: ', taxRate * 100, '%')
print('Return On Capital: ', returnOnCapital, '%')

print()
