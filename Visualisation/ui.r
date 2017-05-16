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
        helpText(HTML("<strong>SV-Pop</strong> is a visualisation tool designed for efficient analysis of population-wide structural variation, in this case for <I>Plasmodium falciparum</I>. The source code for this project is available on <a href='https://github.com/mr664/SV-Pop'>github</a>, alongside the associated analysis pipeline. Both are suitable for analysis of other datasets, providing that structural variants are provided per-individual in <I>DELLY</I> output format.")),
        helpText(HTML("Each plot consists of variant frequency within 1000bp windows, centred upon a given basepair positions. Sub-populations are specified on a continent or sub-continent basis. Further information is present within the association publication: <a href='https://www.google.co.uk'><strong>Ravenhall M <I>et al.</I> 2017. doi: XXXXXXXX</strong></a>")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>How do I customise plots?</strong>")),
        helpText(HTML("Our underlying data considers four types of structural variants (deletions, duplications, insertions and inversions) within the fourteen <I>P. falciparum</I> chromosomes, apicoplast and mitochondria are currently excluded. As such the first control panel concerns selection of these different variant types and chromosomes. Also featured is the ability to select 'Bars' or 'Points' plotting style. By default, this is set to 'Bars', but extended visualisation of specific regions may benefit from the clarify of the 'Points' style.")),
        helpText(HTML("Continent and sub-continent specific sub-populations can be included or excluded through selection within the second control panel, whilst specific positions, frequency cut-offs and the ability to download selected regions (more on this below) are present within the third control panel. Experimentation is encouraged.")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>Can I download variants in a region?</strong>")),
        helpText(HTML("Specific regions can be highlighted by drawing a box with the mouse on the plotting area. Doing so will both identify genes and count variants within that region, but also allow the user to download a .csv file containing those specific variants. This can be download by pressing the 'Download Selected Variants' button within the third control panel.")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>What if I find a bug/have a question?</strong>")),
        helpText(HTML("Bug reports should be submitted via the github repository. Other general enquiries may be directed to <a href='mailto:matt.ravenhall@lshtm.ac.uk?Subject=SV-Pop%20Question'>matt.ravenhall@lshtm.ac.uk</a>."))
      )
    )
  ) # Close tabPanel
) # Close navbarPage

))
