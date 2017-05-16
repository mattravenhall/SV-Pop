# Define UI for application that draws a histogram
shinyUI(fluidPage(

  includeCSS('styles.css'),

  # Application title
  navbarPage("SV-Pop", id="nav", theme='styles.css',
  #titlePanel(HTML("SV-Pop: Plasmodium falciparum")),

  # Sidebar with a slider input for the number of bins
  tabPanel("Explorer",
    fluidRow(
      column(12,
        wellPanel(style="background-color: #ffffff; border: 1px solid grey;",
          plotOutput('distPlot',brush='plot_brush'),
          HTML("<br>"),
          verbatimTextOutput('info')
        )
      ),
      column(3,
        wellPanel(style="border: 1px solid grey;", #background-color: #d1d1d1;
          selectInput('Model', label='Variant Type:',choices = list('Deletions'='DEL', 'Duplications'='DUP','Insertions'='INS','Inversion'='INV')),
          selectInput('Chromosome', label='Chromosome:',choices = list('1'='Pf3D7_01_v3','2'='Pf3D7_02_v3','3'='Pf3D7_03_v3','4'='Pf3D7_04_v3','5'='Pf3D7_05_v3','6'='Pf3D7_06_v3','7'='Pf3D7_07_v3','8'='Pf3D7_08_v3','9'='Pf3D7_09_v3','10'='Pf3D7_10_v3','11'='Pf3D7_11_v3','12'='Pf3D7_12_v3','13'='Pf3D7_13_v3','14'='Pf3D7_14_v3'),selected='Pf3D7_14_v3'),
          selectInput('PlotType', label='Plot Type:',choices = list('Bars'='h','Points'='b'),selected='h')
          )
      ),
      column(3,
        wellPanel(style="border: 1px solid grey;", #background-color: #d1d1d1;
          checkboxGroupInput('Populations', label='Populations: ',choices = list('Africa'='AFR','West Africa'='wAFR', 'Central Africa'='cAFR','East Africa'='eAFR','Asia'='ASI','South Asia'='sASI','Southeast Asia'='eASI','South America'='SAMR'),selected = list('wAFR','cAFR','eAFR','ASI','SAMR'))
          )
      ),
      column(3,
        wellPanel(style="border: 1px solid grey;", #background-color: #d1d1d1;
  #        textInput('xlim','Location (bp):')
          downloadButton('downloadData','Download Selected Variants'),
          helpText(''),
          sliderInput("xlim","Location (bp):",min = 0,max = 3292500,value = c(0,3292500),step=1000),
          sliderInput("ylim","Variant Frequency:",min = 0,max = 1,value = c(0,1))
          )
      ),
      column(3,
        wellPanel(style="border: 1px solid grey;", #background-color: #d1d1d1;
          helpText(HTML("<strong>SV-Pop</strong> is a tool for investigating population-wide structural variation, in this case for <I>Plasmodium falciparum</I>.")),
          helpText(HTML("The analysis pipeline is available at <a href='https://github.com/mr664/SV-Pop'>github</a><strike>, and you can visualise your own output <a href='http://www.google.co.uk'>online</a></strike>.")),
          helpText(HTML("If used, please cite: <strong>Ravenhall M et al. 2017. doi:XXXXXX.</strong>"))
        )
      )
    )
  ), # Close tab panel
  tabPanel('Help',
    column(12,
      wellPanel(style="border: 1px solid grey;",
        helpText(HTML("<strong>What is SV-Pop?</strong>")),
        helpText(HTML("To complete")),
        helpText(HTML("To complete")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>How do I customise plots?</strong>")),
        helpText(HTML("To complete")),
        helpText(HTML("To complete")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>Can I download variants in a region?</strong>")),
        helpText(HTML("To complete")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>What if I find a bug/have a question?</strong>")),
        helpText(HTML("To complete"))
      )
    )
  ) # Close tabPanel
) # Close navbarPage

))
