#!/usr/bin/env python


class instruction():
    iOp='DADD'
    iLabel=None
    iOffset = 0
    rd = 0
    rs = 0
    rt = 0
    def __str__(self):
        return '%s    %s %s,%s,%s' % (self.iLabel,self.iOp,self.rd,self.rs,self.rt)




def parse(inputfile):
    mem = {}
    regs = {}
    new_pc = -1
    

    for i in range (0,32):
        regs[str(i)] = 0
    for i in range(0,1000,8):
        mem[str(i)] = 0

    insts =  []
    state = 'r';
    for line in inputfile:
        line = line.strip()
        if line == "\n":
            state = 'empty'
        elif line == "REGISTERS":
            state = 'r'
        elif line == 'MEMORY':
            state = 'm'
        elif line == 'CODE':
            state = 'c'
        else:
            if state == 'r':
                line = line.strip()
                rs = line.split()
                rn = rs[0][1:]
                val =  rs[1]
                regs[rn] = val
            elif state == 'm':
                line = line.strip()
                ms = line.split()
                mn = ms[0]
                mv = ms[1]
                mem[mn] = mv
            elif state == 'c':
                nIns = instruction()
                if line.find(':') > -1:
                    sp = line.split(':')
                    line = sp[1].strip()
                    nIns.iLabel = sp[0].strip()
                else:
                    pass

                if line.find('BNEZ') > -1:
                    line = line.strip()
                    ppre = line.split(' ',1)
                    rds =  [x.strip() for x in ppre[1].split(',')]
                    nIns.rd = rds[0][1:]
                    nIns.iOp = 'BNEZ'
                    nIns.rs = rds[1][0:]
                    nIns.iType = 'b'
                elif line.find('#') > -1:
                    line = line.strip()
                    ins = line.split(' ',1)
                    nIns.iOp = ins[0].strip()
                    rds = [x.strip() for x in ins[1].split(',')]
                    nIns.rd = rds[0][1:]
                    nIns.rs = rds[1][1:]
                    nIns.rt = rds[2][1:]
                    nIns.iType = 'i'
                elif line.find('(') > -1:
                    line = line.strip()
                    ins = line.split(' ', 1)
                    nIns.iOp = ins[0].strip()
                    rds = [x.strip() for x in ins[1].split(',')]
                    rgx = '/\(([^)]+)\)/'


                    l= rds[1].find('(')
                    r =rds[1].find(')')

                    if(nIns.iOp == 'SD'):
                        nIns.rd = rds[1][l+1:r][1:]
                        nIns.rs =  rds[0][1:]
                    elif(nIns.iOp == 'LD'):

                        nIns.rs = rds[1][l+1:r][1:]
                        nIns.rd = rds[0][1:]
                    else:
                        pass

                    l= rds[1].find('(')

                    nIns.iOffset =  rds[1][:l]

                    nIns.iType = 'm'
                else:
                    line = line.strip()
                    ins = line.split(' ',1)
                    nIns.iOp = ins[0].strip()
                    rds =[x.strip() for x in  ins[1].split(',')]

                    nIns.rd = rds[0][1:]
                    nIns.rs = rds[1][1:]
                    nIns.rt = rds[2][1:]
                    nIns.iType = 'r'
                insts.append(nIns)

    return mem,regs,insts



def inquire_user():

    in_file = raw_input('Enter an input file name: ')
    out_file = raw_input('Enter an output file name: ')

    return in_file, out_file


def  stalled(rn, mem1, mem2):
    if(mem1):
        if (mem1.iOp == 'LD' and mem1.rd == rn):
            return True
    if(mem2):
        if( mem2.iOp == 'LD' and mem2.rd ==rn ):
            return True

    return False



def do_sim(mem,regs,ins):
    clock = 1
    pc = 0
    returnable = ""
    ifs1 = None
    ifs2 = None
    ids  = None
    exs  = None
    mem1 = None
    mem2 = None
    mem3 = None
    delay_ins = None
    wb =  None
    done = False
    bypass = False
    new_pc = -1
    stall = 0
    label_map = {}
    started = False
    counter = {'ifs1':1,'ifs2':0,'ids':0,'exs':0,'mem1':0,'mem2':0,'mem3':0,'wb':0}
    #stalin = ('ex':0,'id':0,'ifs2':0, 'ifs1':0)

    for idx, i in enumerate(ins):
        if i.iType != 'b' and i.iLabel != None:
            label_map[str(i.iLabel)] = idx
        else:
            pass


   

    while wb is not None or mem1 is not None or mem2 is not None or mem3 is not None or exs is not None or ids is not None or ifs2 is not None or ifs1 is not None or not started:
        started = True
        returnable  =  returnable + 'c#'+ str(clock)+' '

        """ Writeback Stage """
        if (wb):
            returnable = returnable + 'I' + str(counter['wb']) + '-WB '

        """ Mem3 Stage """
        if(mem3):

            returnable = returnable + 'I' + str(counter['mem3']) + '-MEM3 '
        """ Mem2 Stage """
        if(mem2):

            if mem2.iOp == 'SD':
                final_mem =  str(int(regs[str(mem2.rd)]) +int( mem2.iOffset))
                mem[str(final_mem)] =   regs[str(mem2.rs)]
            elif mem2.iOp == 'LD':
                final_mem = str(int(regs[str(mem2.rs)]) +int( mem2.iOffset))

                regs[str(mem2.rd)] = mem[final_mem]
            
            
            returnable = returnable + 'I' + str(counter['mem2']) + '-MEM2 '

        """ Mem1 Stage """
        if(mem1):
            if(stall == 0):
                returnable = returnable + 'I' + str(counter['mem1']) + '-MEM1 '

          
        """ Exec Stage """
        if(exs):
            stall = 0
            if(stalled(exs.rt,mem1,mem2) and stalled(exs.rs,mem1,mem2) and False):
                stall =  1
                
            else:
                if exs.iOp == 'DADD':
                    if(stalled(exs.rt,mem1,mem2) or stalled(exs.rs,mem1,mem2)):
                        stall =  1
                    if exs.iType == 'r':
                        regs[str(exs.rd)] =   int(regs[exs.rs])+int(regs[exs.rt])
                    elif exs.iType =='i':

                        regs[str(exs.rd)] =   int(regs[exs.rs])+int(exs.rt)
                elif  exs.iOp == 'SUB':
                    if exs.iType == 'r':
                        regs[str(exs.rd)] =   int(regs[exs.rs]) - int(regs[exs.rt])
                    elif exs.iType =='i':

                        regs[str(exs.rd)] =   int(regs[exs.rs]) - int(exs.rt)
                elif exs.iOp == 'BNEZ':
                    if(stalled(exs.rt,mem1,mem2) or stalled(exs.rs,mem1,mem2)):
                        stall =  1
                    else:
                        
                        rs_num = int(regs[str(exs.rd)])
                        if (rs_num != 0):

                        #Handle Branch
                            new_pc =  label_map[str(exs.rs)]
                        #Flush Pipeline
                        #TODO: Find a better way to flush on the spot
                        
                           # ids = None
                            #ifs2 = None
                            #ifs1 = None
                        #Set pc to new pc
                            pc = new_pc
                            bypass = True
                        
                   
                        else:
                            #bypass = False
                            pass
                
                if(exs):
                    if (stall > 0):
                        returnable = returnable + 'I'+str(counter['exs']) + '-stall '
                        pass
                    else:
                        returnable = returnable + 'I' +str(counter['exs']) + '-EX '


        """ Decode Stage """
        if(ids):
            if(stall > 0):
                returnable = returnable + 'I'+ str(counter['ids']) + '-stall '
            elif(bypass):
                returnable = returnable + 'I' + str(counter['ids']) + '-ID '
                ids = None
            else:
                returnable = returnable + 'I' + str(counter['ids']) + '-ID '

        """ Fetch2 Stage """
   
        if(ifs2):
            
            if(stall > 0):
                returnable = returnable + 'I'+str(counter['ifs2']) + '-stall '
            elif(bypass):
                returnable = returnable + 'I' + str(counter['ifs2']) + '-IF2 '
                ifs2 = None
            else:
                returnable = returnable + 'I' + str(counter['ifs2']) + '-IF2 '
       
      
        """
        if(pc < len(ins) and  stall == 0):
            
            #FIXME: This happens even if a stall is supposed to be here
            ifs1 = ins[pc]
        
         
            new_pc = -1
   
        elif (stall > 0 and pc < len(ins)):
            delay_inst = ins[pc]
            ifs1 = None
        else:
            ifs1 = None
            
     
            
        if(stall == 0):

            pc = pc + 1 
           
            
  
        
        if(ifs1 != None):
            if(stall > 0):  
                returnable = returnable + 'I' + str(ins.index(ifs1)+1) + '-stall '
                
            elif(not bypass):
                returnable = returnable + 'I' + str(ins.index(ifs1)+1) + '-IF1 '
            elif(bypass):
               pass
        else:
            pass     
        
        """
       
        if(stall > 0):

            if(ifs1 == None):
                
                returnable = returnable + 'I' + str(counter['ifs1']) + '-stall '
                pass
               
        elif(bypass):
            ifs1 = None
       
            #bypass = False
            if(ifs1):
                returnable = returnable + 'I' + str(counter['ifs1']) + '-IF1 '
               
                #bypass = False
                new_pc = -1
        else:
            if(pc < len(ins)):
                ifs1 = ins[pc]
                returnable = returnable + 'I' + str(counter['ifs1']) + '-IF1 '
                pc = pc + 1
                
            else:
                ifs1 = None
                


        """ Stall checks and insertion of them """


   
        wb   = mem3
        counter['wb']=counter['mem3']
        mem3 = mem2
        counter['mem3']=counter['mem2']
        mem2 = mem1
        counter['mem2']=counter['mem1']
        mem1 = None
        
        
        if(stall == 0):
            mem1 = exs
            counter['mem1']=counter['exs']
            exs  = ids
            counter['exs']=counter['ids']
            ids  = ifs2
            counter['ids']=counter['ifs2']
            ifs2 = ifs1
            counter['ifs2']=counter['ifs1']
   
        if(stall >0):
            pass
        elif(bypass):
               bypass = False
        elif(stall == 0):
            counter['ifs1'] = counter['ifs1']+1
       
        returnable =  returnable + '\n'
        clock = clock + 1
       
    return returnable,regs,mem


def main():
    print 'MIPSIM PROJECT'
    print 'Copyright 2013 - Howard Grimberg'
    print 'Licensed under the MIT License'
    print 'See LICENSE.txt for Details\n'
    print 'INTERACTIVE MODE'
    
    done =  False
    
    while not done:
        inf,outf = inquire_user()
    
        finf = open(inf,'r')
        mem,regs,ins = parse(finf)
        finf.close()

        res,regs2,mem2= do_sim(mem,regs,ins)
        f = open(outf,'w')
    
        f.write(res+'\n')
    
        f.write("REGISTERS\n")
        
        for key in sorted(regs2.iterkeys()):
            if(regs2[key] != 0):
                f.write( "R%s %s \n" % (key,str( regs2[key])))

                f.write("MEMORY\n")
        for key in sorted(mem2.iterkeys(), reverse=True):
            if(mem2[key] != 0):
                f.write( "%s %s \n" % (key,str( mem2[key])))
    
        f.close()
                
        exit = raw_input('Exit? (y/n) [n]: ')
        if(exit.lower() == 'y'):
            done = True
    

if __name__ == "__main__":
    main();




