library(shiny)

# Load window frequency files
DEL <- as.data.frame(fread('Files/DEL_Windows.csv',sep=','))
DUP <- as.data.frame(fread('Files/DUP_Windows.csv',sep=','))
INS <- as.data.frame(fread('Files/INS_Windows.csv',sep=','))
INV <- as.data.frame(fread('Files/INV_Windows.csv',sep=','))

# Annotation File 
annot <- as.data.frame(fread('Files/annotation.txt',header=T))

# Frequent specific variants files
DELf <- as.data.frame(fread('Files/DEL_FrqIndex.csv',sep=','))
DUPf <- as.data.frame(fread('Files/DUP_FrqIndex.csv',sep=','))
INSf <- as.data.frame(fread('Files/INS_FrqIndex.csv',sep=','))
INVf <- as.data.frame(fread('Files/INV_FrqIndex.csv',sep=','))

# Full variant files
DELv <- as.data.frame(fread('Files/DEL_AllIndex.csv',sep=','))
DUPv <- as.data.frame(fread('Files/DUP_AllIndex.csv',sep=','))
INSv <- as.data.frame(fread('Files/INS_AllIndex.csv',sep=','))
INVv <- as.data.frame(fread('Files/INV_AllIndex.csv',sep=','))

# Define UI for application that draws a histogram
VARs <- rbind(rbind(rbind(DEL, DUP),INS),INV)

annot <- as.data.frame(fread('Files/annotation.txt',header=T))

chrs = list()
for (i in unique(VARs$Chromosome)) { chrs[i] = i }
pops = list()
for (i in names(VARs)[7:dim(VARs)[2]-1]) { pops[i] = i }

ui <- fluidPage(

  includeCSS('www/styles.css'),

  # Application title
  navbarPage("SV-Pop", id="nav", theme='www/styles.css',

  # Sidebar with a slider input for the number of bins
  tabPanel("Explorer",
    fluidRow(
      column(12,
        wellPanel(style="background-color: #ffffff; border: 1px solid grey;",
          plotOutput('distPlot', brush='plot_brush', height='550px'),
          HTML("<br>"),
          verbatimTextOutput('info')
        )
      ),
      column(3,
        wellPanel(style="border: 1px solid grey;", #background-color: #d1d1d1;
          selectInput('Model', label='Variant Type:', choices=list('Deletions'='DEL', 'Duplications'='DUP','Insertions'='INS','Inversion'='INV')),
          selectInput('Chromosome', label='Chromosome:', choices=chrs, selected=chrs[1]),
          selectInput('PlotType', label='Plot Type:', choices=list('Bars'='h','Points'='b'), selected='h')
          )
      ),
      column(3,
        wellPanel(style="border: 1px solid grey;", #background-color: #d1d1d1;
          checkboxGroupInput('Populations', label='Populations: ', choices=pops, selected=sample(pops,min(length(pops)/2, 5)))
          )
      ),
      column(3,
        wellPanel(style="border: 1px solid grey;", #background-color: #d1d1d1;
          downloadButton('downloadData','Download Selected Variants'),
          helpText(''),
          sliderInput("xlim","Location (bp):", min=0, max=max(VARs$End), value=c(0,3292500),step=1000),
          sliderInput("ylim","Variant Frequency:", min=0, max=1, value=c(0,1))
          )
      ),
      column(3,
        wellPanel(style="border: 1px solid grey;", #background-color: #d1d1d1;
          helpText(HTML("<strong>SV-Pop</strong> is a tool for visualising population-wide structural variation.")),
          helpText(HTML("You can find the upstream analysis pipeline on <a href='https://github.com/mattravenhall/SV-Pop'>github</a>.")),
          helpText(HTML("If used, please cite: <strong>Ravenhall M et al. 2018. doi:XXXXXX.</strong>"))
        )
      )
    )
  ), # Close tab panel
  tabPanel('Help',
    column(12,
      wellPanel(style="border: 1px solid grey;",
        helpText(HTML("<strong>What is SV-Pop?</strong>")),
        helpText(HTML("<strong>SV-Pop</strong> is a visualisation tool designed for efficient analysis of population-wide structural variation. The source code for this project is available on <a href='https://github.com/mattravenhall/SV-Pop'>github</a>, alongside the associated analysis pipeline. Combined these provide an effective, high-throughput pipeline for structural variant discovery.")),
        helpText(HTML("Each plot consists of variant frequency within genomic windows, centred upon a given position. Sub-populations are pulled from the user-specified files. Further information is present within the associated publication: <a href='https://www.google.co.uk'><strong>Ravenhall M <I>et al.</I> 2018. doi: XXXXXXXX</strong></a>")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>How do I customise plots?</strong>")),
        helpText(HTML("Our underlying data considers four types of structural variants (deletions, duplications, insertions and inversions) within the fourteen <I>P. falciparum</I> chromosomes, apicoplast and mitochondria are currently excluded. As such the first control panel concerns selection of these different variant types and chromosomes. Also featured is the ability to select 'Bars' or 'Points' plotting style. By default, this is set to 'Bars', but extended visualisation of specific regions may benefit from the clarify of the 'Points' style.")),
        helpText(HTML("Continent and sub-continent specific sub-populations can be included or excluded through selection within the second control panel, whilst specific positions, frequency cut-offs and the ability to download selected regions (more on this below) are present within the third control panel. Experimentation is encouraged.")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>Can I download variants in a region?</strong>")),
        helpText(HTML("Specific regions can be highlighted by drawing a box with the mouse on the plotting area. Doing so will both identify genes and count variants within that region, but also allow the user to download a .csv file containing those specific variants. This can be download by pressing the 'Download Selected Variants' button within the third control panel.")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>Are there any working examples?</strong>")),
        helpText(HTML("We have previously used this analysis and visualisation pipeline to investigate structural variation in <I>Plasmodium falciparum</I>, you can find that work <strong><a href='https://mattravenhall.github.io/example-page'>online XXXXXXX</a></strong>.")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>What if I find a bug/have a question?</strong>")),
        helpText(HTML("Bug reports should be submitted on <a href='https://github.com/mattravenhall/SV-Pop/issues'>github</a>. Other general enquiries may be directed to <a href='mailto:matt.ravenhall@lshtm.ac.uk?Subject=SV-Pop%20Question'>matt.ravenhall@lshtm.ac.uk</a>."))
      )
    )
  ) # Close tabPanel
  ) # Close navbarPage
)

server <- function(input, output) {
  output$distPlot <- renderPlot({
    par(mfrow=c(length(input$Populations),1),mar=c(0,4,0,0))

    toPlot <- get(input$Model)
    toPlot <- toPlot %>% filter(Chromosome == as.character(input$Chromosome))

    x <- toPlot$Start

    labcex = 1.4

    halfWindow <- toPlot$End[1] / 2

    index <- 0
    for (pop in input$Populations) {
      index <- index + 1
      plot(toPlot$Start+halfWindow, toPlot[,pop], pch=20, xlab='Location (Mbp)', ylab=pop, cex.lab=labcex, lend=2, las=1,
           xlim=input$xlim, ylim=input$ylim, type=input$PlotType, col=rainbow(length(input$Populations))[index])
    }
  })
  output$info <- renderText({
      forConversion <- c('deletions','duplications','insertions','inversions')
      names(forConversion) <- c('DEL','DUP','INS','INV')

      xy_range_str <- function(e) {
        if (is.null(e)) return ("No Region Selected\n")
        geneList <- unique(annot[annot$Chromosome == input$Chromosome & annot$Start < e$xmax & annot$End > e$xmin,]$Feature)
        AllIndex <- get(paste(input$Model,'v',sep=''))
        AllIndex <- AllIndex[AllIndex$Chromosome == input$Chromosome & as.numeric(AllIndex$Start) < e$xmax & as.numeric(AllIndex$End) > e$xmin,]
        freqVars <- get(paste(input$Model,'f',sep=''))
        freqVars <- freqVars[freqVars$Chromosome == input$Chromosome & as.numeric(freqVars$Start) < e$xmax & as.numeric(freqVars$End) > e$xmin,]
        assign('currXmin',round(e$xmin),envir=globalenv())
        assign('currXmax',round(e$xmax),envir=globalenv())
        paste0('Highlighted Region: ',format(round(e$xmin,0),big.mark=','), " bp to ", format(round(e$xmax),big.mark=','),' bp\n',format(length(geneList),big.mark=','),' Genes Present: ',
        paste(geneList,collapse=', '),'\n',format(dim(AllIndex)[1],big.mark=','),' distinct ',forConversion[input$Model],' globally (',
        format(dim(freqVars)[1],big.mark=','),' in at least 5% of samples).')
        # Subset an annotation file with input$Chromosome, e$xmin and, e$xmax
      }
      paste0("",xy_range_str(input$plot_brush))
    })
  output$downloadData <- downloadHandler(
      filename = function() {
        paste("variantSubset-",input$Model,':',input$Chromosome,":",currXmin,"-",currXmax,".csv",sep='')
      },
      content = function(file) {
        AllIndex <- as.data.frame(fread(paste('Files/',input$Model,'_Variants.csv',sep=''),sep=','))
        AllIndex <- AllIndex[AllIndex$Chromosome == input$Chromosome & as.numeric(AllIndex$Start) < currXmax & as.numeric(AllIndex$End) > currXmin,]
        write.csv(AllIndex, file)
      }
    )
}

shinyApp(ui, server)