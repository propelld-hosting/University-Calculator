import streamlit as st
import pandas as pd
import numpy_financial as npf
import mysql.connector
from datetime import datetime
import uuid
import numpy as np

# db_config_write = {
#     'user': 'rijul',
#     'password': 'KVyoMT83ClrTmiX',
#     'host': 'db-product-analytics-new.cgrxatb6l23o.ap-south-1.rds.amazonaws.com',
#     'database': 'propelld'
# }
# mydb_write = mysql.connector.connect(**db_config_write)


#file_name = '/Users/propelld/Desktop/University_Calculator/Dashboard/base_tables.xlsx'
file_name = 'base_tables.xlsx'
def load_data(sheet_name):
    return pd.read_excel(file_name, sheet_name=sheet_name, engine='openpyxl')

df_institute_details = load_data('Institute Details')
df_roi = load_data('Institute Details')  # Assuming both sheets have the same name
df_student_income_multiplier = load_data('Student Income Multiplier')
df_student_income_roi = load_data('Student Income ROI')
df_student_tenure = load_data('Student tenure')
df_student_morat = load_data('Student Morat')
df_foir = load_data('FOIR')

df_parent_income_multiplier = load_data('Parent Income Multiplier')
df_bureau_penalty = load_data('Bureau Penalty')
df_parent_tenure = load_data('Parent Tenure')

# df_institute_details = pd.read_excel(file_name,sheet_name = 'Institute Details')
# df_roi = pd.read_excel(file_name,sheet_name = 'Institute Details')
# df_student_income_multiplier = pd.read_excel(file_name, sheet_name='Student Income Multiplier')
# df_student_income_roi = pd.read_excel(file_name,sheet_name='Student Income ROI')
# df_student_tenure = pd.read_excel(file_name,sheet_name= 'Student tenure')
# df_student_morat = pd.read_excel(file_name,sheet_name='Student Morat')
# df_foir = pd.read_excel(file_name,sheet_name='FOIR')

# df_parent_income_multiplier = pd.read_excel(file_name,sheet_name='Parent Income Multiplier')
# df_bureau_penalty = pd.read_excel(file_name,sheet_name='Bureau Penalty')
# df_parent_tenure = pd.read_excel(file_name,sheet_name='Parent Tenure')

def convert_numpy_types(data):
    for key, value in data.items():
        if isinstance(value, (np.integer, np.int64)):
            data[key] = int(value)
        elif isinstance(value, (np.floating, np.float64)):
            data[key] = float(value)
        elif isinstance(value, np.bool_):
            data[key] = bool(value)
        elif pd.isna(value):  # Handle NaN values (convert to None for SQL)
            data[key] = None
    return data

# Title of the app
st.title("University Calculator")

# Function to take input parameters
def input_parameters():
    college_name = st.selectbox("College Name", df_institute_details['Institute Name'].unique())
    filtered_courses = df_institute_details[
        df_institute_details['Institute Name'] == college_name
    ]['Corrected Course'].unique()
    
    course_type = st.selectbox("Course Type", filtered_courses)
    tenure = st.number_input("Remaining Course Tenure (months)", min_value=0)
    student_x = st.number_input("Student X% (percentage)", min_value=0.0, max_value=100.0)
    student_xii = st.number_input("Student XII% (percentage)", min_value=0.0, max_value=100.0)
    student_grad = st.number_input("Student Grad % (percentage)", min_value=0.0, max_value=100.0)
    employment_type = st.selectbox("Parent Employment Type", ["Salaried - State/Central Government Employee", 
                                                             "Salaried - MNC",
                                                             "Salaried - Others",
                                                             "Self Employed - Own Account worker Professional",
                                                             "Self Employed - Own Account worker Non-Professional"])
    profession = st.selectbox("Parent Profession", df_parent_income_multiplier['ITR Income Profession'].unique())
    income = st.number_input("Parent Income on Document (Annual) (In INR)", min_value=0)
    bureau_score = st.number_input("Bureau Score (-1 or 300-900)", min_value=-1, max_value=900)
    obligations = st.number_input("Annual Obligations (INR)", min_value=0)
    
    params = {
        "College Name": college_name,
        "Course Type": course_type,
        "Remaining Course Tenure (months)": tenure,
        "Student X%": student_x,
        "Student XII%": student_xii,
        "Student Grad %": student_grad,
        "Parent Employment Type": employment_type,
        "Parent Profession": profession,
        "Annual Parent Income (INR)": income,
        "Bureau Score": bureau_score,
        "Obligations": obligations
    }
    
    return params




def display_dataframe(params):
    
    result_df = pd.DataFrame()
    
    #Future Income
    college_name = params.get('College Name')
    course_type = params.get('Course Type')
    
    condition = (df_institute_details['Institute Name'] == college_name) & (df_institute_details['Corrected Course'] == course_type)
    
    future_income = round(int(df_institute_details[condition]['Avg. CTC'].iloc[0]/12),0)
    
    result_df.loc['Future Income','Value'] = future_income
    
    
    #Placement %age
    placement_percentage = df_institute_details[condition]['Placement %'].iloc[0]
    
    result_df.loc['Placement %','Value'] = str(round(placement_percentage*100,2)) + '%'
    
    
    #Expected annual increment
    expected_annual_increment_percentage = 0.1
    
    result_df.loc['Expected Annual Increment','Value'] = str(expected_annual_increment_percentage*100) + '%'
    
    
    #Average %age
    student_x = params.get('Student X%')
    student_xii = params.get('Student XII%')
    student_grad = params.get('Student Grad %')
    if course_type == 'MBA/PGDM':
        average_percentage = round((student_x + student_xii + student_grad)/3,2)/100
    else:
        average_percentage = round((student_x + student_xii)/2,2)/100
    
    result_df.loc['Average % (Acad Aggregate)','Value'] = str(round(average_percentage*100,1)) + '%'
    
    
    #Average student income post study
    base = (future_income)*(placement_percentage)
    
    condition1 = df_student_income_multiplier['Student Avg % (Min)'] <= average_percentage/100
    condition2 = df_student_income_multiplier['Student Avg % (Max)'] >= average_percentage/100
    income_multiplier = df_student_income_multiplier[(condition1) & (condition2)]['Student Income Multiplier'].iloc[0]
    
    average_student_income_post_study = base*income_multiplier
    
    result_df.loc['Average Student Income Post Study','Value'] = round(average_student_income_post_study,0)
    
    
    #Rate of Interest
    condition1 = df_student_income_roi['Min'] <= average_student_income_post_study
    condition2 = df_student_income_roi['Max'] >= average_student_income_post_study
    rate_of_interest = df_student_income_roi[(condition1) & (condition2)]['ROI'].iloc[0]
    
    result_df.loc['Rate of Interest','Value'] = str(round(rate_of_interest*100,1)) + '%'
    
    
    
    #Post Study Max Tenure
    condition1 = df_student_tenure['Post study Income (min)'] <= average_student_income_post_study
    condition2 = df_student_tenure['Post study Income (max)'] >= average_student_income_post_study
    
    post_study_max_tenure = df_student_tenure[(condition1) & (condition2)]['Tenure'].iloc[0]
    
    result_df.loc['Post Sudy Max Tenure','Value'] = int(post_study_max_tenure)
    
    
    #Does student qualify for Morat
    condition1 = df_student_morat['Placement % Min'] <= placement_percentage
    condition2 = df_student_morat['Placement% Max'] >= placement_percentage
    condition3 = df_student_morat['Student Avg % Min'] <= average_percentage
    condition4 = df_student_morat['Student Avg % Max'] >= average_percentage
    
    morat = df_student_morat[(condition1) & (condition2) & (condition3) & (condition4)]['Morat'].iloc[0]
    
    result_df.loc['Does Student qualify for Moratorium','Value'] = morat
    
    
    #Course Tenure
    result_df.loc['Course Tenure','Value'] = params.get('Remaining Course Tenure (months)')
    
    
    #Average Income Over Loan Tenure
    a = (1+expected_annual_increment_percentage)
    b = (post_study_max_tenure/12)
    
    average_income_over_loan_tenure = (average_student_income_post_study*((pow(a,b)-1)/expected_annual_increment_percentage))/b
    
    result_df.loc['Average Income over loan tenure','Value'] = round(average_income_over_loan_tenure,1)
    
    
    #FOIR
    condition1 = df_foir['Min'] <= average_student_income_post_study 
    condition2 = df_foir['Max'] >= average_student_income_post_study 
    
    foir = df_foir[(condition1) & (condition2)]['FOIR'].iloc[0]
    
    result_df.loc['FOIR','Value'] = str(round(foir*100,1)) + '%'
    
    
    #Monthly EMI serviceability by student
    monthly_emi_serviceability_by_student = average_income_over_loan_tenure*foir
    result_df.loc['Monthly EMI serviceability by student','Value'] = round(monthly_emi_serviceability_by_student,1)
    
    
    #Loan Eligibility - Student Based
    rate = rate_of_interest/12
    nper = post_study_max_tenure
    pmt =   0
    fv = -npf.pv(rate,nper,monthly_emi_serviceability_by_student)
    
    final_pv = -npf.pv(rate,nper,pmt,fv)
    
    if pd.notna(final_pv):
        loan_eligibility_student_based = final_pv
    else:
        loan_eligibility_student_based = ''
    
    result_df.loc['Loan Eligibility - Student Based','Value'] = round(loan_eligibility_student_based,0)
    
    
    #Avg. EMI during Morat
    if morat.lower() == 'yes':
        average_emi_during_morat = ((loan_eligibility_student_based*rate_of_interest)/2)/12
    else:
        average_emi_during_morat = 0
        
    result_df.loc['Avg. EMI during Morat','Value'] = round(average_emi_during_morat,1)
    
    
    
    #Loan Eligibility - Parent Only
    rate = rate_of_interest/12
    nper = params.get('Remaining Course Tenure (months)')
    pmt =   5000-average_emi_during_morat
    
    if average_emi_during_morat < 5000:
        loan_eligibility_parent = -npf.pv(rate,nper,pmt)
    else:
        loan_eligibility_parent = 0
    
    result_df.loc['Loan Eligibility - Parent Only','Value'] = round(loan_eligibility_parent,1)
    
    
    #Total Loan Eligibility
    if average_emi_during_morat > 5000:
        total_loan_eligibility = (5000/average_emi_during_morat)*loan_eligibility_student_based
    else:
        total_loan_eligibility = loan_eligibility_student_based
    
    result_df.loc['Total Loan Eligibility','Value'] = round(total_loan_eligibility,0)
    
    
    #Tenure - Student Eligibility
    tenure_student_eligibility = post_study_max_tenure + params.get('Remaining Course Tenure (months)')
    
    result_df.loc['Tenure - Student Eligibility','Value'] = round(tenure_student_eligibility,0)
    
    
    
    
    #XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    #BREAK BREAK BREAK BREAK BREAK
    
    
    result_df_parent = pd.DataFrame()
    
    #Parent Income
    monthly_income = params.get('Annual Parent Income (INR)')/12
    
    condition = df_parent_income_multiplier['ITR Income Profession'] == params.get('Parent Profession')
    income_multipier = df_parent_income_multiplier[condition]['Multiplier'].iloc[0]
    
    condition1 = df_bureau_penalty['Bureau Score (Min)'] <= params.get('Bureau Score')
    condition2 = df_bureau_penalty['Bureau Score (Max)'] >= params.get('Bureau Score')
    
    bureau_multiplier = df_bureau_penalty[(condition1) & (condition2)]['Multiplier'].iloc[0]
    
    parent_income = monthly_income*income_multipier*bureau_multiplier
    
    result_df_parent.loc['Parent Income','Value'] = round(parent_income,0)
    
    
    
    #Max Tenure based on Parent
    condition1 = df_parent_tenure['Post study Income (min)'] <= parent_income
    condition2 = df_parent_tenure['Post study Income (max)'] >= parent_income
    
    max_tenure_parent = df_parent_tenure[(condition1) & (condition2)]['Tenure'].iloc[0]
    
    result_df_parent.loc['Max Tenure based on Parent','Value'] = round(max_tenure_parent,0)
    
    
    #Max Tenure (Parent+Student)
    max_tenure_parent_student = max(max_tenure_parent,tenure_student_eligibility)
    
    result_df_parent.loc['Max Tenure - Parent + student','Value'] = round(max_tenure_parent_student,0)
    
    
    
    #Parent Average Income estimate over loan tenure
    a = (1+expected_annual_increment_percentage)
    b = (max_tenure_parent_student/12)
    
    parent_average_income_over_loan_tenure = (parent_income*((pow(a,b)-1)/expected_annual_increment_percentage))/b
    
    result_df_parent.loc['Parent Average Income Estimate over loan tenure','Value'] = round(parent_average_income_over_loan_tenure,0)
    
    
    #Average Current EMI Obligations
    annual_emi_obligations = params.get('Obligations')
    result_df_parent.loc['Annual Current EMI obligations','Value'] = annual_emi_obligations
    
    
    
    #Average EMI Obligations
    a = (1+expected_annual_increment_percentage)
    b = (max_tenure_parent/12)
    
    average_emi_obligations = (annual_emi_obligations*((pow(a,b)-1)/expected_annual_increment_percentage))/b
    
    result_df_parent.loc['Average EMI Obligations','Value'] = round(average_emi_obligations,0)
    
    
    #FOIR Parent
    condition1 = df_foir['Min'] <= parent_income
    condition2 = df_foir['Max'] >= parent_income
    
    foir_parent = df_foir[(condition1) & (condition2)]['FOIR'].iloc[0]
    
    result_df_parent.loc['FOIR','Value'] = str(round(foir_parent*100,1)) + '%'
    
    
    #Eduction EMI Serviceability
    education_emi_serviceability = (parent_average_income_over_loan_tenure*foir_parent) - average_emi_obligations - 5000    
    education_emi_serviceability = max(education_emi_serviceability,0)
    
    result_df_parent.loc['Education EMI Serviceability','Value'] = round(education_emi_serviceability,0)
    
    
    #Top up LA serviceable by Parent
    rate = rate_of_interest/12
    nper = max_tenure_parent
    pmt =   -education_emi_serviceability
    
    topup_la_serviceable_by_parent = npf.pv(rate,nper,pmt)
    
    result_df_parent.loc['Top up LA serviceable by Parent','Value'] = round(topup_la_serviceable_by_parent,0)
    
    
    #XXXXXXXXXXXXXXXXXXXXXXXXX
    #Final df
    
    final_df = pd.DataFrame()
    
    #Max LA - Parent + Student
    max_loan_amount_parent_student = total_loan_eligibility + topup_la_serviceable_by_parent
    
    final_df.loc['Max LA - Parent + Student','Value'] = round(max_loan_amount_parent_student,0)
    
    
    #Max Tenure - Parent+student
    final_df.loc['Max Tenure - Parent + Student','Value'] = round(max_tenure_parent_student,0)
    
    
    #Can Morat Be Provided
    final_df.loc['Can Morat be provided','Value'] = morat
    

    
    
    
    return final_df ,result_df,result_df_parent

def main():
    st.write("Input details")
    
    params = input_parameters()
    

    if st.button("Evaluate", key="evaluate_button"):
        
        st.write("")
        st.write("Final Result")
        # Convert to table for proper left alignment
        final_df ,result_df,result_df_parent = display_dataframe(params)
        st.dataframe(final_df,width=500)
        
        st.write("")
        st.write("Student")
        st.dataframe(result_df,width=500)
        
        st.write("")
        st.write("Parent")
        st.dataframe(result_df_parent,width=500)

        
        
    
        # #WRITING IN DB
        # #INPUT
        # record_id = str(uuid.uuid4())
        # current_timestamp = datetime.now()
        
        # # Construct the SQL INSERT statement
        # insert_query = """
        #     INSERT INTO InputUniversityCalculator (
        #         Id,
        #         CollegeName,
        #         CourseType,
        #         RemainingCourseTenure,
        #         Student10Percentage,
        #         Student12Percentage,
        #         StudentGradPercentage,
        #         ParentEmploymentType,
        #         ParentProfession,
        #         AnnualParentIncome,
        #         BureauScore,
        #         AnnualObligations,
        #         UpdateTimeStamp_IST
        #     ) 
        #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        # """

        # values = (
        #     record_id,
        #     params["College Name"],
        #     params["Course Type"],
        #     params["Remaining Course Tenure (months)"],
        #     params["Student X%"],
        #     params["Student XII%"],
        #     params["Student Grad %"],
        #     params["Parent Employment Type"],
        #     params["Parent Profession"],
        #     params["Annual Parent Income (INR)"],
        #     params["Bureau Score"],
        #     params["Obligations"],
        #     current_timestamp
        # )

        # mydb_write.cursor().execute(insert_query, values)
        # mydb_write.commit()
        
        
        
        
        # #OUTPUT
        # current_time = datetime.now()

        # # Example values from DataFrames
        # final_df_values = {
        #     "MaxLA_Parent_Student": final_df.loc['Max LA - Parent + Student', 'Value'],
        #     "MaxTenure_Parent_Student": final_df.loc['Max Tenure - Parent + Student', 'Value'],
        #     "MoratAvailable": final_df.loc['Can Morat be provided', 'Value'],
        # }
        
        # result_df_values = {
        #     "FutureIncome": result_df.loc['Future Income', 'Value'],
        #     "ExpectedAnnualIncrement": result_df.loc['Expected Annual Increment', 'Value'],
        #     "AverageAcadPercentage": result_df.loc['Average % (Acad Aggregate)', 'Value'],
        #     "AverageStudentIncomePostStudy": result_df.loc['Average Student Income Post Study', 'Value'],
        #     "RateOfInterest": result_df.loc['Rate of Interest', 'Value'],
        #     "PostStudyMaxTenure": result_df.loc['Post Sudy Max Tenure', 'Value'],
        #     "CourseTenure": result_df.loc['Course Tenure', 'Value'],
        #     "AverageIncomeOverLoanTenure": result_df.loc['Average Income over loan tenure', 'Value'],
        #     "FOIRStudent": result_df.loc['FOIR', 'Value'],
        #     "MonthlyEMIServiceabilityByStudent": result_df.loc['Monthly EMI serviceability by student', 'Value'],
        #     "LoanEligibilityStudentBased": result_df.loc['Loan Eligibility - Student Based', 'Value'],
        #     "AverageEMIDuringMorat": result_df.loc['Avg. EMI during Morat', 'Value'],
        #     "LoanEligibilityParentOnly": result_df.loc['Loan Eligibility - Parent Only', 'Value'],
        #     "TotalLoanEligibility": result_df.loc['Total Loan Eligibility', 'Value'],
        #     "TenureStudentEligibility": result_df.loc['Tenure - Student Eligibility', 'Value'],
        # }
        
        # result_df_parent_values = {
        #     "ParentIncome": result_df_parent.loc['Parent Income', 'Value'],
        #     "MaxTenureBasedOnParent": result_df_parent.loc['Max Tenure based on Parent', 'Value'],
        #     "MaxTenureParent_Student": result_df_parent.loc['Max Tenure - Parent + student', 'Value'],
        #     "ParentAverageIncomeEstimateOverLoanTenure": result_df_parent.loc['Parent Average Income Estimate over loan tenure', 'Value'],
        #     "AnnualCurrentEMIObligations": result_df_parent.loc['Annual Current EMI obligations', 'Value'],
        #     "AverageEMIObligations": result_df_parent.loc['Average EMI Obligations', 'Value'],
        #     "FOIRParent": result_df_parent.loc['FOIR', 'Value'],
        #     "EducationEMIServiceability": result_df_parent.loc['Education EMI Serviceability', 'Value'],
        #     "TopUpLAServiceableByParent": result_df_parent.loc['Top up LA serviceable by Parent', 'Value'],
        # }
        
        # # Combine all values into one dictionary
        # values = {**final_df_values, **result_df_values, **result_df_parent_values}
        
        # # SQL insert query
        # insert_query = """
        #     INSERT INTO OutputUniversityCalculator (
        #         InputId,
        #         MaxLA_Parent_Student,
        #         MaxTenure_Parent_Student,
        #         MoratAvailable,
        #         FutureIncome,
        #         ExpectedAnnualIncrement,
        #         AverageAcadPercentage,
        #         AverageStudentIncomePostStudy,
        #         RateOfInterest,
        #         PostStudyMaxTenure,
        #         CourseTenure,
        #         AverageIncomeOverLoanTenure,
        #         FOIRStudent,
        #         MonthlyEMIServiceabilityByStudent,
        #         LoanEligibilityStudentBased,
        #         AverageEMIDuringMorat,
        #         LoanEligibilityParentOnly,
        #         TotalLoanEligibility,
        #         TenureStudentEligibility,
        #         ParentIncome,
        #         MaxTenureBasedOnParent,
        #         MaxTenureParent_Student,
        #         ParentAverageIncomeEstimateOverLoanTenure,
        #         AnnualCurrentEMIObligations,
        #         AverageEMIObligations,
        #         FOIRParent,
        #         EducationEMIServiceability,
        #         TopUpLAServiceableByParent,
        #         UpdateTimeStamp_IST
        #     ) VALUES (
        #         %(InputId)s,
        #         %(MaxLA_Parent_Student)s,
        #         %(MaxTenure_Parent_Student)s,
        #         %(MoratAvailable)s,
        #         %(FutureIncome)s,
        #         %(ExpectedAnnualIncrement)s,
        #         %(AverageAcadPercentage)s,
        #         %(AverageStudentIncomePostStudy)s,
        #         %(RateOfInterest)s,
        #         %(PostStudyMaxTenure)s,
        #         %(CourseTenure)s,
        #         %(AverageIncomeOverLoanTenure)s,
        #         %(FOIRStudent)s,
        #         %(MonthlyEMIServiceabilityByStudent)s,
        #         %(LoanEligibilityStudentBased)s,
        #         %(AverageEMIDuringMorat)s,
        #         %(LoanEligibilityParentOnly)s,
        #         %(TotalLoanEligibility)s,
        #         %(TenureStudentEligibility)s,
        #         %(ParentIncome)s,
        #         %(MaxTenureBasedOnParent)s,
        #         %(MaxTenureParent_Student)s,
        #         %(ParentAverageIncomeEstimateOverLoanTenure)s,
        #         %(AnnualCurrentEMIObligations)s,
        #         %(AverageEMIObligations)s,
        #         %(FOIRParent)s,
        #         %(EducationEMIServiceability)s,
        #         %(TopUpLAServiceableByParent)s,
        #         %(UpdateTimeStamp_IST)s
        #     )
        # """
        
        # values['InputId'] = record_id
        # values['UpdateTimeStamp_IST'] = current_time
        
        # # Convert NumPy types in the `values` dictionary
        # values = convert_numpy_types(values)

        # # Add unique keys and timestamp to the dictionary
        # values['InputId'] = record_id
        # values['UpdateTimeStamp_IST'] = current_time
        
        # # Execute the query
        # mydb_write.cursor().execute(insert_query, values)
        # mydb_write.commit()


if __name__ == "__main__":
    main()
