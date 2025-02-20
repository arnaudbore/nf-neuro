process SEGMENTATION_FASTSURFER {
    tag "$meta.id"
    label 'process_single'

    container "${ 'deepmi/fastsurfer:cpu-v2.2.0' }"
    containerOptions {
        (workflow.containerEngine == 'docker') ? '--entrypoint ""' : ''
    }

    input:
        tuple val(meta), path(anat), path(fs_license)

    output:
        tuple val(meta), path("*_fastsurfer")       , emit: fastsurferdirectory
        path "versions.yml"                         , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def acq3T = task.ext.acq3T ? "--3T" : ""
    def FASTSURFER_HOME = "/fastsurfer"
    def SUBJECTS_DIR = "${prefix}_fastsurfer"
    """
    mkdir ${prefix}_fastsurfer/
    $FASTSURFER_HOME/run_fastsurfer.sh  --allow_root \
                                        --sd \$(realpath ${SUBJECTS_DIR}) \
                                        --fs_license \$(realpath $fs_license) \
                                        --t1 \$(realpath ${anat}) \
                                        --sid ${prefix} \
                                        --seg_only --py python3 \
                                        ${acq3T}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        fastsurfer: \$($FASTSURFER_HOME/run_fastsurfer.sh --version)
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def FASTSURFER_HOME = "/fastsurfer"

    """
    mkdir ${prefix}_fastsurfer/

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        fastersurfer: \$($FASTSURFER_HOME/run_fastsurfer.sh --version)
    END_VERSIONS

    function handle_code () {
    local code=\$?
    ignore=( 1 )
    exit \$([[ " \${ignore[@]} " =~ " \$code " ]] && echo 0 || echo \$code)
    }
    trap 'handle_code' ERR

    $FASTSURFER_HOME/run_fastsurfer.sh --version
    """
}
