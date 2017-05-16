# Define server logic required to draw a histogram
shinyServer(function(input, output) {

  # Load window frequency files
  DEL <- as.data.frame(fread('Files/DEL_Windows.csv',sep=','))
  DUP <- as.data.frame(fread('Files/DUP_Windows.csv',sep=','))
  INS <- as.data.frame(fread('Files/INS_Windows.csv',sep=','))
  INV <- as.data.frame(fread('Files/INV_Windows.csv',sep=','))

  # Annotation File
  annot <- as.data.frame(fread('Files/Pf3D7_annotation.txt',header=T))

  # Frequent specific variants files
  DELf <- as.data.frame(fread('Files/DEL_freq5.csv',sep=','))
  DUPf <- as.data.frame(fread('Files/DUP_freq5.csv',sep=','))
  INSf <- as.data.frame(fread('Files/INS_freq5.csv',sep=','))
  INVf <- as.data.frame(fread('Files/INV_freq5.csv',sep=','))

  # Full variant files
  DELv <- as.data.frame(fread('Files/DEL_AllVars.csv',sep=','))
  DUPv <- as.data.frame(fread('Files/DUP_AllVars.csv',sep=','))
  INSv <- as.data.frame(fread('Files/INS_AllVars.csv',sep=','))
  INVv <- as.data.frame(fread('Files/INV_AllVars.csv',sep=','))

  output$distPlot <- renderPlot({
    par(mfrow=c(length(input$Populations),1),mar=c(0,4,0,0))

    toPlot <- get(input$Model)
    toPlot <- toPlot %>% filter(Chromosome == as.character(input$Chromosome)) ### NEED TO SUB-SET BY CHROMOSOME, BUT BREAKS ATM

    x <- toPlot$Start

    WAFR <- c('Burkina_Faso','Gambia_The','Ghana','Guinea','Mali','Nigeria')
    CAFR <- c('Cameroon','DRC')
    EAFR <- c('Kenya','Madagascar','Malawi','Tanzania','Uganda')
    AFR <- c(WAFR,CAFR,EAFR)

    SASI <- c('Bangladesh')
    EASI <- c('Cambodia','Laos','PNG','Myanmar','Thailand','Vietnam')
    ASI <- c(SASI,EASI)

    SAMR <- c('Colombia','Peru')

    nAFR <- 1926
    nWAFR <- 986
    nCAFR <- 413
    nEAFR <- 527

    nASI <- 1945
    nSASI <- 66
    nEASI <- 1879

    nSAMR <- 31

    yWAFR <- rowSums(toPlot[WAFR])
    yCAFR <- rowSums(toPlot[CAFR])
    yEAFR <- rowSums(toPlot[EAFR])
    yAFR <- rowSums(toPlot[AFR])

    ySASI <- rowSums(toPlot[SASI])
    yEASI <- rowSums(toPlot[EASI])
    yASI <- rowSums(toPlot[ASI])

    ySAMR <- rowSums(toPlot[SAMR])

    labcex = 1.4

    # Fst values should probably go here
    if ('AFR' %in% input$Populations) {
     plot(x+500, yAFR/nAFR, pch=20, xlab='Location (Mbp)', ylab='Africa', cex.lab=labcex,
           xlim=input$xlim, ylim=input$ylim, type=input$PlotType,col='darkred',lend=2,las=1) }
    if ('wAFR' %in% input$Populations) {
     plot(x+500, yWAFR/nWAFR, pch=20, xlab='Location (Mbp)', ylab='W. Africa', cex.lab=labcex,
          xlim=input$xlim, ylim=input$ylim, type=input$PlotType,col='red',lend=2,las=1) }
    if ('cAFR' %in% input$Populations) {
     plot(x+500, yCAFR/nCAFR, pch=20, xlab='Location (Mbp)', ylab='C. Africa', cex.lab=labcex,
          xlim=input$xlim, ylim=input$ylim, type=input$PlotType,col='goldenrod',lend=2,las=1) }
    if ('eAFR' %in% input$Populations) {
     plot(x+500, yEAFR/nEAFR, pch=20, xlab='Location (Mbp)', ylab='E. Africa', cex.lab=labcex,
          xlim=input$xlim, ylim=input$ylim, type=input$PlotType,col='darkgreen',lend=2,las=1) }
    if ('ASI' %in% input$Populations) {
     plot(x+500, yASI/nASI, pch=20, xlab='Location (Mbp)', ylab='Asia', cex.lab=labcex,
          xlim=input$xlim, ylim=input$ylim, type=input$PlotType,col=rainbow(7)[5],lend=2,las=1) }
    if ('sASI' %in% input$Populations) {
     plot(x+500, yASI/nASI, pch=20, xlab='Location (Mbp)', ylab='S. Asia', cex.lab=labcex,
           xlim=input$xlim, ylim=input$ylim, type=input$PlotType,col=rainbow(7)[6],lend=2,las=1) }
    if ('eASI' %in% input$Populations) {
     plot(x+500, yASI/nASI, pch=20, xlab='Location (Mbp)', ylab='SE. Asia', cex.lab=labcex,
          xlim=input$xlim, ylim=input$ylim, type=input$PlotType,col='purple',lend=2,las=1) }
    if ('SAMR' %in% input$Populations) {
     plot(x+500, ySAMR/nSAMR, pch=20, xlab='Location (Mbp)', ylab='S. America', cex.lab=labcex,
          xlim=input$xlim, ylim=input$ylim, type=input$PlotType,col='grey40',lend=2,las=1) }
  })
  output$info <- renderText({
      forConversion <- c('deletions','duplications','insertions','inversions')
      names(forConversion) <- c('DEL','DUP','INS','INV')

      xy_range_str <- function(e) {
        if (is.null(e)) return ("No Region Selected\n")
        geneList <- unique(annot[annot$Chromosome == input$Chromosome & annot$Start < e$xmax & annot$End > e$xmin,]$Feature)
        allVars <- get(paste(input$Model,'v',sep=''))
        allVars <- allVars[allVars$Chromosome == input$Chromosome & as.numeric(allVars$Start) < e$xmax & as.numeric(allVars$End) > e$xmin,]
        freqVars <- get(paste(input$Model,'f',sep=''))
        freqVars <- freqVars[freqVars$Chromosome == input$Chromosome & as.numeric(freqVars$Start) < e$xmax & as.numeric(freqVars$End) > e$xmin,]
        assign('currXmin',round(e$xmin),envir=globalenv())
        assign('currXmax',round(e$xmax),envir=globalenv())
        paste0('Highlighted Region: ',format(round(e$xmin,0),big.mark=','), " bp to ", format(round(e$xmax),big.mark=','),' bp\n',format(length(geneList),big.mark=','),' Genes Present: ',
        paste(geneList,collapse=', '),'\n',format(dim(allVars)[1],big.mark=','),' distinct ',forConversion[input$Model],' globally (',
        format(dim(freqVars)[1],big.mark=','),' in at least 5% of samples).')
        # Subset an annotation file with input$Chromosome, e$xmin and, e$xmax
      }
      paste0("",xy_range_str(input$plot_brush))
    }
    )
  output$downloadData <- downloadHandler(
      filename = function() {
        paste("variantSubset-",input$Model,':',input$Chromosome,":",currXmin,"-",currXmax,".csv",sep='')
      },
      content = function(file) {
        allVars <- as.data.frame(fread(paste('Files/',input$Model,'_VarsForDownload.csv',sep=''),sep=','))
        allVars <- allVars[allVars$Chromosome == input$Chromosome & as.numeric(allVars$Start) < currXmax & as.numeric(allVars$End) > currXmin,]
        write.csv(allVars, file)
      }
    )
})
