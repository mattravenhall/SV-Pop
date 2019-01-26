library(shiny)

models <- c('Deletions','Duplications','Insertions','Inversions')
names(models) <- c('DEL','DUP','INS','INV')

# Check which SV models are present
missingModel <- c()
for (model in names(models)) {
  if (!file.exists(paste('Files/',model,'_Variants.csv',sep=''))) {
    print(paste('Warning: Variant file for',model,'not found, skipping SV type.',sep=' '))
    missingModel <- c(missingModel, model)
  } else if (!file.exists(paste('Files/',model,'_Windows.csv',sep=''))) {
    print(paste('Warning: Windows file for',model,'not found, skipping SV type.',sep=' '))
    missingModel <- c(missingModel, model)
  } else if (!file.exists(paste('Files/',model,'_AllIndex.csv',sep=''))) {
    print(paste('Warning: Full Index file for',model,'not found, skipping SV type.',sep=' '))
    missingModel <- c(missingModel, model)
  } else if (!file.exists(paste('Files/',model,'_FrqIndex.csv',sep=''))) {
    print(paste('Warning: Frequent Index file for',model,'not found, skipping SV type.',sep=' '))
    missingModel <- c(missingModel, model)
  } 
}
print(missingModel)
if (length(missingModel) == length(names(models))) {
  print('Error: Missing files for all models.')
  quit()
} else {
  models <- models[!(names(models) %in% missingModel)]
}

# Annotation File, if it exists
if (!file.exists('Files/annotation.txt')) {
  print('Error: Annotation file missing.')
  quit()
} else {
  annot <- as.data.frame(fread('Files/annotation.txt',header=T))   
}

# Load files for each model
for (model in names(models)) {
  assign(model, as.data.frame(fread(paste('Files/',model,'_Windows.csv',sep=''),sep=',')))
  assign(paste(model,'f',sep=''), as.data.frame(fread(paste('Files/',model,'_FrqIndex.csv',sep=''),sep=',')))
  assign(paste(model,'v',sep=''), as.data.frame(fread(paste('Files/',model,'_AllIndex.csv',sep=''),sep=',')))
  }

# Define UI for application that draws a histogram
if (length(models) == 1) {
  VARs <- get(names(models[1]))
} else if (length(models) >= 2) {
  for (model in names(models)[2:length(names(models))]) {
    if (model == names(models[2])) {
      VARs <- rbind(get(names(models)[1]), get(names(models)[2]))
    } else {
      VARs <- rbind(VARS, get(model))
    }
  }
}

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
          selectInput('Model', label='Variant Type:', choices=lapply(split(names(models), models), unname)),
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
          helpText(HTML("You can find the upstream analysis pipeline, and further documentation, on <a href='https://github.com/mattravenhall/SV-Pop' target='_blank'>github</a>."))
          # , helpText(HTML("If used, please cite: <strong>Ravenhall M et al. doi:XXXXXX.</strong>"))
        )
      )
    )
  ), # Close tab panel
  tabPanel('Help',
    column(12,
      wellPanel(style="border: 1px solid grey;",
        helpText(HTML("<strong>What is SV-Pop?</strong>")),
        helpText(HTML("<strong>SV-Pop</strong> is a visualisation tool designed for efficient analysis of population-wide structural variation. The source code for this project is available on <a href='https://github.com/mattravenhall/SV-Pop' target='_blank'>github</a>, alongside the associated analysis pipeline. Combined, these provide an effective, high-throughput pipeline for structural variant discovery. Each plot consists of variant frequency within genomic windows, as presented in the standard SV-Pop windows format. Sub-populations are pulled from the user-provided files.")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>How do I customise plots?</strong>")),
        helpText(HTML("Visualised data considers of up to four types of structural variants (deletions, duplications, insertions and inversions) within any number of chromosomes. As such the first control panel concerns selection of these different variant types and chromosomes. Also featured is the ability to select 'Bars' or 'Points' plotting style. By default, this is set to 'Bars', but extended visualisation of specific regions may benefit from the clarify of the 'Points' style (particularly for data-dense regions).")),
        helpText(HTML("Continent and sub-continent specific sub-populations can be included or excluded through selection within the second control panel, whilst specific positions, frequency cut-offs and the ability to download selected regions (more on this below) are present within the third control panel. Experimentation is encouraged.")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>Can I subset to variants in a region?</strong>")),
        helpText(HTML("Specific regions can be highlighted by drawing a box with the mouse on the plotting area. Doing so will identify both genes and count variants within that region, but also allow the user to download a .csv file containing those specific variants. To produce this, simply click the 'Download Selected Variants' button within the third control panel.")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>Are there any working examples?</strong>")),
        helpText(HTML("A test dataset is provided within the SV-Pop repo, details regarding its use can be found in the <a href='https://github.com/mattravenhall/SV-Pop/wiki/Visualisation-Expanded-Help#Running-the-Test-Set' target='_blank'>wiki</a>.")),
        helpText(HTML("<br>")),
        helpText(HTML("<strong>What if I find a bug/have a question?</strong>")),
        helpText(HTML("Bug reports should be submitted on <a href='https://github.com/mattravenhall/SV-Pop/issues' target='_blank'>github</a>. Other general enquiries may be directed to <a href='mailto:matt.ravenhall@lshtm.ac.uk?Subject=SV-Pop%20Question'>matt.ravenhall@lshtm.ac.uk</a>."))
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
      # forConversion <- c('deletions','duplications','insertions','inversions')
      # names(forConversion) <- c('DEL','DUP','INS','INV')
      forConversion <<- "models"

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